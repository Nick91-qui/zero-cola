from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import GradeSourceType, UserRole
from app.models.exam import Exam
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamQuestionCreate, QuestionCreate
from app.services.auth import AuthService
from app.services.exam import ExamService

client = TestClient(app)


def _collect_keys(payload):
    if isinstance(payload, dict):
        keys = set(payload.keys())
        for value in payload.values():
            keys.update(_collect_keys(value))
        return keys
    if isinstance(payload, list):
        keys = set()
        for item in payload:
            keys.update(_collect_keys(item))
        return keys
    return set()


def _student_headers(
    test_db_session,
    *,
    email: str = "student_api_online@cola-zero.edu",
    student_code: str = "88888",
):
    service = AuthService(test_db_session)
    password_hash = service.hash_password("studentpass123")
    user = User(
        email=email,
        password_hash=password_hash,
        role=UserRole.STUDENT,
        student_code=student_code,
    )
    test_db_session.add(user)
    test_db_session.commit()
    login_payload = type(
        "UserLogin",
        (),
        {"email": email, "password": "studentpass123"},
    )()
    token = service.authenticate_user(login_payload)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _teacher_and_published_exam(test_db_session):
    teacher = User(
        email="teacher_api_online@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    test_db_session.add(teacher)
    test_db_session.commit()

    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="API online exam",
            total_questions=2,
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
    return service.publish_exam(exam.id)


def test_online_attempt_api_flow_and_confidentiality(override_get_db, test_db_session):
    exam = _teacher_and_published_exam(test_db_session)
    student_headers = _student_headers(test_db_session)

    start_response = client.post(
        "/api/v1/attempts/start",
        json={"exam_id": str(exam.id)},
        headers=student_headers,
    )
    assert start_response.status_code == 201
    start_data = start_response.json()
    assert start_data["attempt"]["status"] == "in_progress"
    assert start_data["current_question"]["question_number"] == 1
    assert "correct_answer" not in _collect_keys(start_data)
    assert "correct_answers" not in start_data["attempt"]
    assert "incorrect_answers" not in start_data["attempt"]
    assert "accuracy_percentage" not in start_data["attempt"]
    assert "raw_score" not in start_data["attempt"]
    assert "final_score" not in start_data["attempt"]

    current_question = start_data["current_question"]
    answer_key_item = (
        test_db_session.query(Exam).filter(Exam.id == exam.id).one().answer_key.items[0]
    )
    assert current_question["statement"] == answer_key_item.statement

    save_response = client.put(
        f"/api/v1/attempts/{start_data['attempt']['id']}/answers/1",
        json={"selected_option": answer_key_item.correct_answer},
        headers=student_headers,
    )
    assert save_response.status_code == 200
    save_data = save_response.json()
    assert save_data["current_question"]["question_number"] == 2
    assert "correct_answer" not in _collect_keys(save_data)

    next_response = client.post(
        f"/api/v1/attempts/{start_data['attempt']['id']}/next/1",
        headers=student_headers,
    )
    assert next_response.status_code == 200
    assert next_response.json()["current_question"]["question_number"] == 2

    previous_response = client.post(
        f"/api/v1/attempts/{start_data['attempt']['id']}/previous/2",
        headers=student_headers,
    )
    assert previous_response.status_code == 200
    assert previous_response.json()["current_question"]["question_number"] == 1

    submit_response = client.post(
        f"/api/v1/attempts/{start_data['attempt']['id']}/submit",
        headers=student_headers,
    )
    assert submit_response.status_code == 200
    result_data = submit_response.json()
    assert result_data["grade"]["source_type"] == GradeSourceType.ONLINE.value
    assert result_data["attempt"]["status"] == "graded"
    assert "correct_answer" not in _collect_keys(result_data)
    assert "correct_answers" in result_data["attempt"]

    result_response = client.get(
        f"/api/v1/attempts/{start_data['attempt']['id']}/result",
        headers=student_headers,
    )
    assert result_response.status_code == 200
    assert result_response.json()["grade"]["source_type"] == GradeSourceType.ONLINE.value


def test_online_attempt_api_enforces_student_isolation(override_get_db, test_db_session):
    exam = _teacher_and_published_exam(test_db_session)
    student_headers = _student_headers(
        test_db_session,
        email="student_one@cola-zero.edu",
        student_code="88888",
    )
    other_student_headers = _student_headers(
        test_db_session,
        email="student_two@cola-zero.edu",
        student_code="99999",
    )

    start_response = client.post(
        "/api/v1/attempts/start",
        json={"exam_id": str(exam.id)},
        headers=student_headers,
    )
    assert start_response.status_code == 201
    attempt_id = start_response.json()["attempt"]["id"]

    forbidden = client.get(f"/api/v1/attempts/{attempt_id}/current", headers=other_student_headers)
    assert forbidden.status_code == 403
