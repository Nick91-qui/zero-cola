from tempfile import SpooledTemporaryFile

import pytest
from starlette.datastructures import UploadFile

from app.api.routes.omr import upload_scan_batch
from app.models.enums import UserRole
from app.models.exam import Exam
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.omr import OMRScanUpdate, OMRTemplateCreate
from app.services.auth import AuthService
from app.services.exam import ExamService
from app.services.omr import OMRService
from tests.test_omr_service import (
    create_multi_page_pdf_bytes,
    create_synthetic_sheet_bytes,
)


def create_teacher_headers(test_db_session, email: str, password: str) -> dict[str, str]:
    service = AuthService(test_db_session)
    user_create = type(
        "UserCreate",
        (),
        {
            "email": email,
            "password": password,
            "role": UserRole.TEACHER,
        },
    )()
    password_hash = service.hash_password(password)

    repo = UserRepository(test_db_session)
    user = repo.create(user_create, password_hash)
    access_token = service.create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers(test_db_session):
    """Creates a teacher user and returns authorization headers."""
    return create_teacher_headers(test_db_session, "teacher_api@cola-zero.edu", "teacherpass123")


@pytest.fixture
def student_user(test_db_session):
    """Creates a student user with OMR code."""
    student = User(
        email="student_api@cola-zero.edu",
        password_hash="fake_hash",
        role=UserRole.STUDENT,
        student_code="77777",
    )
    test_db_session.add(student)
    test_db_session.commit()
    return student


def test_omr_api_workflow(override_get_db, test_db_session, student_user, tmp_path):
    teacher = User(
        email="teacher_api@cola-zero.edu",
        password_hash="fake_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    teacher = (
        test_db_session.query(User)
        .filter(User.email == "teacher_api@cola-zero.edu")
        .one()
    )
    omr_service = OMRService(test_db_session)
    template = omr_service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
            correct_answers={"1": "A", "2": "B", "3": "C"},
        ),
        teacher_id=teacher.id,
    )
    template_id = template.id
    assert template.layout_version == "v1_std_20q"

    pdf_bytes = omr_service.get_template_pdf(
        template_id,
        student_code="77777",
        owner_id=teacher.id,
    )
    assert pdf_bytes.startswith(b"%PDF")

    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="77777", answers={"1": "A", "2": "B", "3": "C"}
    )

    scan = omr_service.process_scan_upload(
        template_id,
        sheet_bytes,
        "scan.png",
        owner_id=teacher.id,
    )
    scan_id = scan.id

    assert scan.status == "success"
    assert scan.student_code == "77777"
    assert scan.student_id == student_user.id
    assert float(scan.score) == 1.50  # 3 out of 20 correct -> 1.50

    fetched_scan = omr_service.get_scan(scan_id, owner_id=teacher.id)
    assert fetched_scan is not None
    assert fetched_scan.id == scan_id

    updated_scan = omr_service.update_scan_manual(
        scan_id,
        OMRScanUpdate(detected_answers={"1": "A", "2": "B", "3": "D"}),
        owner_id=teacher.id,
    )
    assert updated_scan.detected_answers["3"] == "D"
    assert float(updated_scan.score) == 1.00

    grade = omr_service.confirm_scan(scan_id, teacher.id, owner_id=teacher.id)

    assert grade.student_id == student_user.id
    assert float(grade.score) == 1.00
    assert grade.source_type == "OMR"
    assert grade.source_id == scan_id


def test_omr_api_template_isolation_between_teachers(
    override_get_db,
    test_db_session,
    student_user,
):
    create_teacher_headers(test_db_session, "teacher_a@cola-zero.edu", "teacherpass-a")
    create_teacher_headers(test_db_session, "teacher_b@cola-zero.edu", "teacherpass-b")
    teacher_a = test_db_session.query(User).filter(User.email == "teacher_a@cola-zero.edu").one()
    teacher_b = test_db_session.query(User).filter(User.email == "teacher_b@cola-zero.edu").one()

    omr_service = OMRService(test_db_session)
    exam_service = ExamService(test_db_session)
    template_a = omr_service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
            correct_answers={"1": "A", "2": "B"},
        ),
        teacher_id=teacher_a.id,
    )
    template_b = omr_service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
        ),
        teacher_id=teacher_b.id,
    )
    template_a_id = template_a.id
    template_b_id = template_b.id

    listed_a = omr_service.list_templates(owner_id=teacher_a.id)
    assert [item.id for item in listed_a] == [template_a_id]

    listed_b = omr_service.list_templates(owner_id=teacher_b.id)
    assert [item.id for item in listed_b] == [template_b_id]

    assert omr_service.get_template(template_a_id, owner_id=teacher_b.id) is None

    with pytest.raises(ValueError):
        omr_service.get_template_pdf(template_a_id, student_code="77777", owner_id=teacher_b.id)

    with pytest.raises(ValueError):
        omr_service.get_template_preview_png(
            template_a_id,
            student_code="77777",
            owner_id=teacher_b.id,
        )

    with pytest.raises(ValueError):
        omr_service.process_scan_upload(
            template_a_id,
            create_synthetic_sheet_bytes("77777", {"1": "A"}),
            "scan.png",
            owner_id=teacher_b.id,
        )

    scan = omr_service.process_scan_upload(
        template_a_id,
        create_synthetic_sheet_bytes("77777", {"1": "A"}),
        "scan.png",
        owner_id=teacher_a.id,
    )
    scan_id = scan.id

    assert omr_service.get_scan(scan_id, owner_id=teacher_b.id) is None

    with pytest.raises(ValueError):
        omr_service.update_scan_manual(
            scan_id,
            OMRScanUpdate(detected_answers={"1": "A"}),
            owner_id=teacher_b.id,
        )

    with pytest.raises(ValueError):
        omr_service.confirm_scan(scan_id, teacher_b.id, owner_id=teacher_b.id)

    exam = test_db_session.query(Exam).filter(Exam.omr_template_id == template_a_id).one()

    assert exam_service.get_exam(exam.id, teacher_id=teacher_b.id) is None

    with pytest.raises(ValueError):
        exam_service.get_exam_statistics(exam.id, teacher_id=teacher_b.id)

    with pytest.raises(ValueError):
        exam_service.export_exam_pdf(exam.id, teacher_id=teacher_b.id)

    owner_stats = exam_service.get_exam_statistics(exam.id, teacher_id=teacher_a.id)
    assert owner_stats["exam_id"] == exam.id

    owner_confirm = omr_service.confirm_scan(scan_id, teacher_a.id, owner_id=teacher_a.id)
    assert owner_confirm.source_id == scan_id

    forbidden_delete = omr_service.delete_template(template_a_id, owner_id=teacher_b.id)
    assert forbidden_delete is False

    owner_delete = omr_service.delete_template(template_a_id, owner_id=teacher_a.id)
    assert owner_delete is True


@pytest.mark.asyncio
async def test_omr_api_batch_upload_processes_pdf_pages(
    override_get_db,
    test_db_session,
    student_user,
):
    teacher_user = User(
        email="teacher_api_global@cola-zero.edu",
        password_hash="fake_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher_user)
    test_db_session.commit()

    omr_service = OMRService(test_db_session)
    template = omr_service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
            correct_answers={"1": "A", "2": "B"},
        ),
        teacher_id=teacher_user.id,
    )

    pdf_bytes = create_multi_page_pdf_bytes(
        student_code="77777",
        pages=[
            {"1": "A", "2": "B"},
            {"1": "A", "2": "C"},
        ],
    )
    upload_buffer = SpooledTemporaryFile()
    upload_buffer.write(pdf_bytes)
    upload_buffer.seek(0)
    upload_file = UploadFile(file=upload_buffer, filename="batch.pdf")

    payload = await upload_scan_batch(
        omr_template_id=template.id,
        file=upload_file,
        current_user=teacher_user,
        db=test_db_session,
    )

    assert payload["omr_template_id"] == template.id
    assert payload["total_pages"] == 2
    assert len(payload["scans"]) == 2
    assert {scan["status"] for scan in payload["scans"]} == {"success"}
    assert all(scan["student_id"] == student_user.id for scan in payload["scans"])


def test_omr_list_and_preview(override_get_db, test_db_session):
    teacher = User(
        email="teacher_api@cola-zero.edu",
        password_hash="fake_hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    teacher = (
        test_db_session.query(User)
        .filter(User.email == "teacher_api@cola-zero.edu")
        .one()
    )
    omr_service = OMRService(test_db_session)
    template = omr_service.create_template(
        OMRTemplateCreate(
            layout_version="v1_std_20q",
            total_questions=20,
            options_per_question=5,
            correct_answers={"1": "A"},
        ),
        teacher_id=teacher.id,
    )
    template_id = template.id

    listed = omr_service.list_templates(owner_id=teacher.id)
    assert any(item.id == template_id for item in listed)

    preview_bytes = omr_service.get_template_preview_png(
        template_id,
        student_code="77777",
        owner_id=teacher.id,
    )
    assert preview_bytes[:8] == b"\x89PNG\r\n\x1a\n"
