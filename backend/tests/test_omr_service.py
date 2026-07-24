from decimal import Decimal

import cv2
import numpy as np

from app.core.omr_layouts import DrawingElementType, get_layout_provider
from app.models.enums import GradeSourceType, OMRScanStatus, UserRole
from app.models.user import User
from app.schemas.omr import OMRScanUpdate, OMRTemplateCreate
from app.services.omr import OMRService


def create_synthetic_sheet_bytes(student_code: str, answers: dict) -> bytes:
    """Generates synthetic page bytes for v1_std_20q with specified code and answers."""
    page_w, page_h = 1000, 1414
    margin = 50
    canvas_w = page_w + 2 * margin
    canvas_h = page_h + 2 * margin
    img = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

    provider = get_layout_provider("v1_std_20q")
    elements = provider.render(student_code)

    for elem in elements:
        x = int(elem.coordinates[0] + margin)
        y = int(elem.coordinates[1] + margin)

        if elem.type == DrawingElementType.ANCHOR:
            cv2.circle(img, (x, y), 15, (0, 0, 0), -1)

        elif elem.type == DrawingElementType.BUBBLE:
            is_filled = elem.is_filled
            if elem.question_num is not None:
                q_num = elem.question_num
                opt_lbl = elem.option_label
                if str(q_num) in answers and answers[str(q_num)] == opt_lbl:
                    is_filled = True

            cv2.circle(img, (x, y), 8, (0, 0, 0), 1)
            if is_filled:
                cv2.circle(img, (x, y), 8, (0, 0, 0), -1)
            else:
                cv2.circle(img, (x, y), 7, (255, 255, 255), -1)

    success, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()


def test_omr_service_template_lifecycle(test_db_session):
    service = OMRService(test_db_session)

    template_in = OMRTemplateCreate(
        layout_version="v1_std_20q",
        total_questions=20,
        options_per_question=5,
        correct_answers={"1": "A", "2": "B"},
    )

    template = service.create_template(template_in)
    assert template.id is not None
    assert template.layout_version == "v1_std_20q"

    fetched = service.get_template(template.id)
    assert fetched is not None
    assert fetched.total_questions == 20
    assert fetched.correct_answers == {"1": "A", "2": "B"}


def test_omr_service_process_and_grade(test_db_session, tmp_path):
    # Setup folders
    upload_dir = str(tmp_path / "scans")
    service = OMRService(test_db_session, upload_dir=upload_dir)

    # 1. Create a student in database
    student = User(
        email="student_omr@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.STUDENT,
        student_code="10234",
    )
    test_db_session.add(student)

    # 2. Create template
    template_in = OMRTemplateCreate(
        layout_version="v1_std_20q",
        total_questions=20,
        options_per_question=5,
        correct_answers={"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"},
    )
    template = service.create_template(template_in)
    test_db_session.commit()

    # 3. Generate synthetic sheet bytes
    # Fill Q1=A, Q2=B, Q3=C (correct), Q4=A, Q5=B (incorrect) -> 3 correct out of 20 = 1.5 score
    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="10234", answers={"1": "A", "2": "B", "3": "C", "4": "A", "5": "B"}
    )

    # 4. Process Scan
    scan = service.process_scan_upload(template.id, sheet_bytes, "scan1.png")

    assert scan.id is not None
    assert scan.status == OMRScanStatus.SUCCESS
    assert scan.student_code == "10234"
    assert scan.student_id == student.id
    assert scan.score == Decimal("1.50")  # (3/20)*10 = 1.50
    assert scan.detected_answers["1"] == "A"
    assert scan.detected_answers["4"] == "A"


def test_omr_service_update_and_confirm(test_db_session, tmp_path):
    upload_dir = str(tmp_path / "scans")
    service = OMRService(test_db_session, upload_dir=upload_dir)

    student = User(
        email="student_omr2@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.STUDENT,
        student_code="12345",
    )
    teacher = User(
        email="teacher_omr@cola-zero.edu", password_hash="pass_hash", role=UserRole.TEACHER
    )
    test_db_session.add_all([student, teacher])

    template_in = OMRTemplateCreate(
        layout_version="v1_std_20q", total_questions=20, correct_answers={"1": "A", "2": "B"}
    )
    template = service.create_template(template_in)
    test_db_session.commit()

    # Process scan with student not yet matched
    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="99999",  # no user has this code
        answers={"1": "A", "2": "B"},
    )
    scan = service.process_scan_upload(template.id, sheet_bytes, "scan2.png")

    # Should flag as review needed because student wasn't found
    assert scan.status == OMRScanStatus.REVIEW_NEEDED
    assert scan.student_id is None

    # Teacher manually updates the student code to "12345" and changes answer Q2 to "C"
    update_in = OMRScanUpdate(
        student_code="12345",
        detected_answers={"1": "A", "2": "C"},  # 1 correct, 1 incorrect out of 20 -> 0.5 score
    )
    updated_scan = service.update_scan_manual(scan.id, update_in)

    assert updated_scan.student_id == student.id
    assert updated_scan.student_code == "12345"
    assert updated_scan.score == Decimal("0.50")

    # Teacher confirms scan
    grade = service.confirm_scan(scan.id, teacher.id)

    assert grade.id is not None
    assert grade.student_id == student.id
    assert grade.teacher_id == teacher.id
    assert grade.score == Decimal("0.50")
    assert grade.source_type == GradeSourceType.OMR
    assert grade.source_id == scan.id

    # Scan status should now be SUCCESS
    assert scan.status == OMRScanStatus.SUCCESS
