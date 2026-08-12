from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth import AuthService

client = TestClient(app)


def _register_user(
    *,
    email: str,
    password: str,
    role: str,
    student_code: str | None = None,
) -> dict:
    payload = {"email": email, "password": password, "role": role}
    if student_code is not None:
        payload["student_code"] = student_code
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_admin_user(test_db_session, *, email: str, password: str) -> User:
    admin = User(
        email=email,
        password_hash=AuthService(test_db_session).hash_password(password),
        role=UserRole.ADMIN,
    )
    test_db_session.add(admin)
    test_db_session.commit()
    return admin


def _login_headers(email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_search_participants_and_inactive_are_hidden(
    override_get_db,
    test_db_session,
):
    _create_admin_user(
        test_db_session,
        email="admin_searcher@cola-zero.edu",
        password="admin-search-pass",
    )
    _register_user(
        email="teacher_target@cola-zero.edu",
        password="teacher-target-pass",
        role="teacher",
    )
    _register_user(
        email="student_target@cola-zero.edu",
        password="student-target-pass",
        role="student",
        student_code="24680",
    )
    _register_user(
        email="student_hidden@cola-zero.edu",
        password="student-hidden-pass",
        role="student",
        student_code="13579",
    )
    hidden_student = (
        test_db_session.query(User)
        .filter(User.email == "student_hidden@cola-zero.edu")
        .one()
    )
    hidden_student.is_active = False
    test_db_session.commit()

    headers = _login_headers("admin_searcher@cola-zero.edu", "admin-search-pass")

    teacher_search = client.get(
        "/api/v1/users/search",
        params={"q": "target", "role": "teacher"},
        headers=headers,
    )
    assert teacher_search.status_code == 200, teacher_search.text
    teacher_payload = teacher_search.json()
    assert [item["email"] for item in teacher_payload] == ["teacher_target@cola-zero.edu"]
    assert teacher_payload[0]["role"] == "teacher"

    student_search = client.get(
        "/api/v1/users/search",
        params={"q": "student", "role": "student"},
        headers=headers,
    )
    assert student_search.status_code == 200, student_search.text
    student_payload = student_search.json()
    assert [item["email"] for item in student_payload] == ["student_target@cola-zero.edu"]
    assert student_payload[0]["student_code"] == "24680"


def test_student_cannot_access_user_search(override_get_db, test_db_session):
    _register_user(
        email="student_reader@cola-zero.edu",
        password="student-reader-pass",
        role="student",
        student_code="11111",
    )
    headers = _login_headers("student_reader@cola-zero.edu", "student-reader-pass")

    response = client.get(
        "/api/v1/users/search",
        params={"q": "teacher", "role": "teacher"},
        headers=headers,
    )
    assert response.status_code == 403


def test_teacher_cannot_access_user_search(override_get_db, test_db_session):
    _register_user(
        email="teacher_reader@cola-zero.edu",
        password="teacher-reader-pass",
        role="teacher",
    )
    headers = _login_headers("teacher_reader@cola-zero.edu", "teacher-reader-pass")

    response = client.get(
        "/api/v1/users/search",
        params={"q": "student", "role": "student"},
        headers=headers,
    )
    assert response.status_code == 403


def test_admin_can_create_teacher_and_student_accounts(override_get_db, test_db_session):
    _create_admin_user(
        test_db_session,
        email="admin_creator@cola-zero.edu",
        password="admin-creator-pass",
    )
    headers = _login_headers("admin_creator@cola-zero.edu", "admin-creator-pass")

    teacher_response = client.post(
        "/api/v1/users",
        json={
            "email": "teacher_created@cola-zero.edu",
            "password": "teacher-created-pass",
            "role": "teacher",
        },
        headers=headers,
    )
    assert teacher_response.status_code == 201, teacher_response.text
    teacher_payload = teacher_response.json()
    assert teacher_payload["email"] == "teacher_created@cola-zero.edu"
    assert teacher_payload["role"] == "teacher"
    assert teacher_payload["student_code"] is None

    student_response = client.post(
        "/api/v1/users",
        json={
            "email": "student_created@cola-zero.edu",
            "password": "student-created-pass",
            "role": "student",
            "student_code": "54321",
        },
        headers=headers,
    )
    assert student_response.status_code == 201, student_response.text
    student_payload = student_response.json()
    assert student_payload["email"] == "student_created@cola-zero.edu"
    assert student_payload["role"] == "student"
    assert student_payload["student_code"] == "54321"


def test_non_admin_cannot_create_users(override_get_db, test_db_session):
    _register_user(
        email="teacher_creator_blocked@cola-zero.edu",
        password="teacher-creator-pass",
        role="teacher",
    )
    headers = _login_headers("teacher_creator_blocked@cola-zero.edu", "teacher-creator-pass")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "blocked@cola-zero.edu",
            "password": "blocked-pass",
            "role": "teacher",
        },
        headers=headers,
    )
    assert response.status_code == 403
