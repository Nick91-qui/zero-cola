"""Authorization and data-isolation regression tests for the exam endpoint.

Verifies that students cannot access correct_answer, question details,
draft exams, or archived exams through GET /exams/{exam_id}.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamQuestionCreate, QuestionCreate
from app.services.class_service import ClassService
from app.services.exam import ExamService

client = TestClient(app)


def _register_user(*, email: str, password: str, role: UserRole, student_code: str | None = None):
    payload = {
        "email": email,
        "password": password,
        "role": role.value,
    }
    if student_code is not None:
        payload["student_code"] = student_code
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _login_user(email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _student_headers(
    test_db_session,
    *,
    email: str = "student_isolation@cola-zero.edu",
    student_code: str = "77777",
):
    _register_user(
        email=email,
        password="studentpass123",
        role=UserRole.STUDENT,
        student_code=student_code,
    )
    test_db_session.query(User).filter(User.email == email).one()
    return _login_user(email, "studentpass123")


def _create_published_exam(test_db_session):
    teacher = User(
        email="teacher_isolation@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    admin = User(
        email="admin_isolation@cola-zero.edu",
        password_hash="hash",
        role=UserRole.ADMIN,
    )
    test_db_session.add_all([teacher, admin])
    test_db_session.commit()

    class_service = ClassService(test_db_session)
    class_obj = class_service.create_class(
        current_user=admin,
        name="Turma isolamento",
        academic_period="2026",
        teacher_id=teacher.id,
    )

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Isolation Test Exam",
            total_questions=2,
            class_ids=[class_obj.id],
            questions=[
                ExamQuestionCreate(
                    display_order=1,
                    question=QuestionCreate(
                        statement="Questão 1",
                        options={"A": "A", "B": "B"},
                        correct_answer="A",
                    ),
                ),
                ExamQuestionCreate(
                    display_order=2,
                    question=QuestionCreate(
                        statement="Questão 2",
                        options={"A": "A", "B": "B"},
                        correct_answer="B",
                    ),
                ),
            ],
        ),
        teacher_id=teacher.id,
    )
    return service.publish_exam(exam.id), class_obj, teacher


def _create_draft_exam(test_db_session):
    teacher = User(
        email="teacher_draft_iso@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    admin = User(
        email="admin_draft_iso@cola-zero.edu",
        password_hash="hash",
        role=UserRole.ADMIN,
    )
    test_db_session.add_all([teacher, admin])
    test_db_session.commit()

    class_service = ClassService(test_db_session)
    class_obj = class_service.create_class(
        current_user=admin,
        name="Turma rascunho",
        academic_period="2026",
        teacher_id=teacher.id,
    )

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Draft Isolation Exam",
            total_questions=1,
            class_ids=[class_obj.id],
            questions=[
                ExamQuestionCreate(
                    display_order=1,
                    question=QuestionCreate(
                        statement="Draft Q1",
                        correct_answer="C",
                    ),
                ),
            ],
        ),
        teacher_id=teacher.id,
    )
    return exam, class_obj, teacher


def test_student_cannot_see_correct_answer_on_published_exam(override_get_db, test_db_session):
    exam, class_obj, teacher = _create_published_exam(test_db_session)
    headers = _student_headers(test_db_session)
    admin = (
        test_db_session.query(User).filter(User.email == "admin_isolation@cola-zero.edu").one()
    )
    student = (
        test_db_session.query(User).filter(User.email == "student_isolation@cola-zero.edu").one()
    )
    ClassService(test_db_session).add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[student.id],
    )

    response = client.get(f"/api/v1/exams/{exam.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "correct_answer" not in data
    assert "questions" not in data
    assert "exam_questions" not in data
    assert "explanation" not in data
    assert data["status"] == "published"
    assert data["is_active"] is True


def test_student_cannot_access_draft_exam(override_get_db, test_db_session):
    exam, class_obj, teacher = _create_draft_exam(test_db_session)
    headers = _student_headers(test_db_session)
    admin = (
        test_db_session.query(User).filter(User.email == "admin_draft_iso@cola-zero.edu").one()
    )
    student = (
        test_db_session.query(User).filter(User.email == "student_isolation@cola-zero.edu").one()
    )
    ClassService(test_db_session).add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[student.id],
    )

    response = client.get(f"/api/v1/exams/{exam.id}", headers=headers)
    assert response.status_code == 404


def test_student_cannot_access_archived_exam(override_get_db, test_db_session):
    exam, class_obj, teacher = _create_published_exam(test_db_session)
    service = ExamService(test_db_session)
    service.archive_exam(exam.id)

    headers = _student_headers(test_db_session)
    admin = (
        test_db_session.query(User).filter(User.email == "admin_isolation@cola-zero.edu").one()
    )
    student = (
        test_db_session.query(User).filter(User.email == "student_isolation@cola-zero.edu").one()
    )
    ClassService(test_db_session).add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[student.id],
    )
    response = client.get(f"/api/v1/exams/{exam.id}", headers=headers)
    assert response.status_code == 404


def test_student_cannot_list_exams(override_get_db, test_db_session):
    _create_published_exam(test_db_session)
    headers = _student_headers(test_db_session)

    response = client.get("/api/v1/exams", headers=headers)
    assert response.status_code == 403


def test_student_cannot_access_statistics(override_get_db, test_db_session):
    exam, class_obj, teacher = _create_published_exam(test_db_session)
    headers = _student_headers(test_db_session)
    admin = (
        test_db_session.query(User).filter(User.email == "admin_isolation@cola-zero.edu").one()
    )
    student = (
        test_db_session.query(User).filter(User.email == "student_isolation@cola-zero.edu").one()
    )
    ClassService(test_db_session).add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[student.id],
    )

    response = client.get(f"/api/v1/exams/{exam.id}/statistics", headers=headers)
    assert response.status_code == 403


def test_student_cannot_access_exports(override_get_db, test_db_session):
    exam, class_obj, teacher = _create_published_exam(test_db_session)
    headers = _student_headers(test_db_session)
    admin = (
        test_db_session.query(User).filter(User.email == "admin_isolation@cola-zero.edu").one()
    )
    student = (
        test_db_session.query(User).filter(User.email == "student_isolation@cola-zero.edu").one()
    )
    ClassService(test_db_session).add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[student.id],
    )

    pdf_res = client.get(f"/api/v1/exams/{exam.id}/export/pdf", headers=headers)
    assert pdf_res.status_code == 403

    xlsx_res = client.get(f"/api/v1/exams/{exam.id}/export/xlsx", headers=headers)
    assert xlsx_res.status_code == 403
