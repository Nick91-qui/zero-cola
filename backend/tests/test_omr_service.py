from decimal import Decimal

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.attempt import Attempt, AttemptAnswer
from app.models.enums import GradeSourceType, OMRScanStatus, UserRole
from app.models.exam import Exam
from app.models.omr import OMRTemplate
from app.models.user import User
from app.schemas.omr import OMRScanUpdate, OMRTemplateCreate
from app.services.omr import OMRService
from app.services.omr_sheet_image import render_sheet_png


def create_synthetic_sheet_bytes(student_code: str, answers: dict) -> bytes:
    """Generates synthetic page bytes for v1_std_20q with specified code and answers."""
    return render_sheet_png("v1_std_20q", student_code=student_code, answers=answers)


def test_omr_service_template_lifecycle(test_db_session):
    teacher = User(
        email="teacher_template@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = OMRService(test_db_session)

    template_in = OMRTemplateCreate(
        layout_version="v1_std_20q",
        total_questions=20,
        options_per_question=5,
        correct_answers={"1": "A", "2": "B"},
    )

    template = service.create_template(template_in, teacher_id=teacher.id)
    assert template.id is not None
    assert template.layout_version == "v1_std_20q"
    assert template.exam_id is not None
    assert template.created_by == teacher.id

    fetched = service.get_template(template.id)
    assert fetched is not None
    assert fetched.total_questions == 20
    assert not hasattr(fetched, "correct_answers")
    assert fetched.exam_id == template.exam_id
    assert fetched.created_by == teacher.id

    exam = test_db_session.query(Exam).filter(Exam.id == template.exam_id).first()
    assert exam is not None
    assert exam.answer_key is not None
    assert len(exam.answer_key.items) == 2


def test_omr_service_filters_templates_by_owner(test_db_session):
    teacher_a = User(
        email="teacher_owner_a@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    teacher_b = User(
        email="teacher_owner_b@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add_all([teacher_a, teacher_b])
    test_db_session.commit()

    service = OMRService(test_db_session)

    template = service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
        ),
        teacher_id=teacher_a.id,
    )

    assert service.get_template(template.id, owner_id=teacher_a.id) is not None
    assert service.get_template(template.id, owner_id=teacher_b.id) is None
    assert [tmpl.id for tmpl in service.list_templates(owner_id=teacher_a.id)] == [template.id]
    assert service.list_templates(owner_id=teacher_b.id) == []


def test_omr_service_process_and_grade(test_db_session, tmp_path):
    upload_dir = str(tmp_path / "scans")
    service = OMRService(test_db_session, upload_dir=upload_dir)

    student = User(
        email="student_omr@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.STUDENT,
        student_code="10234",
    )
    teacher = User(
        email="teacher_omr@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add_all([student, teacher])
    test_db_session.commit()

    template = service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
            correct_answers={"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"},
        ),
        teacher_id=teacher.id,
    )

    answer_key_item = (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == template.exam_id, AnswerKeyItem.item_number == 3)
        .first()
    )
    assert answer_key_item is not None
    answer_key_item.correct_answer = "D"
    test_db_session.commit()

    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="10234",
        answers={"1": "A", "2": "B", "3": "D", "4": "A", "5": "B"},
    )

    scan = service.process_scan_upload(template.id, sheet_bytes, "scan1.png")

    assert scan.id is not None
    assert scan.status == OMRScanStatus.SUCCESS
    assert scan.student_code == "10234"
    assert scan.student_id == student.id
    assert scan.score == Decimal("1.50")
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
        email="teacher_omr@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add_all([student, teacher])
    test_db_session.commit()

    template = service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A", "2": "B"},
        ),
        teacher_id=teacher.id,
    )
    answer_key_item = (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == template.exam_id, AnswerKeyItem.item_number == 2)
        .first()
    )
    assert answer_key_item is not None
    answer_key_item.correct_answer = "C"
    test_db_session.commit()

    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="99999",
        answers={"1": "A", "2": "B"},
    )
    scan = service.process_scan_upload(template.id, sheet_bytes, "scan2.png")

    assert scan.status == OMRScanStatus.REVIEW_NEEDED
    assert scan.student_id is None
    assert scan.score == Decimal("0.50")

    update_in = OMRScanUpdate(
        student_code="12345",
        detected_answers={"1": "A", "2": "C"},
    )
    updated_scan = service.update_scan_manual(scan.id, update_in)

    assert updated_scan.student_id == student.id
    assert updated_scan.student_code == "12345"
    assert updated_scan.score == Decimal("1.00")

    grade = service.confirm_scan(scan.id, teacher.id)

    assert grade.id is not None
    assert grade.student_id == student.id
    assert grade.teacher_id == teacher.id
    assert grade.score == Decimal("1.00")
    assert grade.source_type == GradeSourceType.OMR
    assert grade.source_id == scan.id

    assert scan.status == OMRScanStatus.SUCCESS

    attempt = test_db_session.query(Attempt).filter(Attempt.omr_scan_id == scan.id).one()
    exam = test_db_session.query(Exam).filter(Exam.id == template.exam_id).one()
    assert attempt.answer_key_id == exam.answer_key.id
    assert attempt.source == "OMR"

    attempt_answers = (
        test_db_session.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id)
        .order_by(AttemptAnswer.question_number)
        .all()
    )
    assert [row.answer_key_item_id for row in attempt_answers] == [
        item.id for item in exam.answer_key.items
    ]
    assert all(row.answered_at is not None for row in attempt_answers)


def test_omr_service_multiple_attempts_share_answer_key(test_db_session, tmp_path):
    upload_dir = str(tmp_path / "scans")
    service = OMRService(test_db_session, upload_dir=upload_dir)

    student = User(
        email="student_multi@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.STUDENT,
        student_code="33333",
    )
    teacher = User(
        email="teacher_multi@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add_all([student, teacher])
    test_db_session.commit()

    template = service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A", "2": "B"},
        ),
        teacher_id=teacher.id,
    )

    first_sheet = create_synthetic_sheet_bytes(
        student_code="33333",
        answers={"1": "A", "2": "B"},
    )
    second_sheet = create_synthetic_sheet_bytes(
        student_code="33333",
        answers={"1": "A", "2": "C"},
    )

    first_scan = service.process_scan_upload(template.id, first_sheet, "scan-a.png")
    second_scan = service.process_scan_upload(template.id, second_sheet, "scan-b.png")

    service.confirm_scan(first_scan.id, teacher.id)
    service.confirm_scan(second_scan.id, teacher.id)

    attempts = (
        test_db_session.query(Attempt)
        .filter(Attempt.exam_id == template.exam_id, Attempt.student_id == student.id)
        .order_by(Attempt.created_at)
        .all()
    )
    assert len(attempts) == 2
    assert attempts[0].answer_key_id == attempts[1].answer_key_id
    assert attempts[0].id != attempts[1].id


def test_omr_service_missing_answer_key_fails(test_db_session, tmp_path):
    upload_dir = str(tmp_path / "scans")
    service = OMRService(test_db_session, upload_dir=upload_dir)

    student = User(
        email="student_missing_key@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.STUDENT,
        student_code="44444",
    )
    teacher = User(
        email="teacher_missing_key@cola-zero.edu",
        password_hash="pass_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add_all([student, teacher])
    test_db_session.commit()

    exam = Exam(
        title="Prova sem gabarito",
        teacher_id=teacher.id,
        total_questions=20,
        is_active=True,
    )
    test_db_session.add(exam)
    test_db_session.commit()

    template = OMRTemplate(
        exam_id=exam.id,
        layout_version="v1_std_20q",
        total_questions=20,
    )
    test_db_session.add(template)
    test_db_session.commit()

    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="44444",
        answers={"1": "A"},
    )

    scan = service.process_scan_upload(template.id, sheet_bytes, "missing-key.png")

    assert scan.status == OMRScanStatus.FAILED
    assert scan.error_message is not None
    assert "AnswerKey" in scan.error_message
