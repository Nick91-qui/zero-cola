from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.models.audit_log import AuditLog
from app.models.enums import UserRole
from app.models.user import User
from tests.helpers import create_user

client = TestClient(app)


def _register_user(
    *,
    test_db_session,
    email: str,
    password: str,
    role: str,
    student_code: str | None = None,
) -> dict:
    return create_user(
        test_db_session,
        email=email,
        password=password,
        role=UserRole(role),
        student_code=student_code,
    )


def _create_admin_user(test_db_session, *, email: str, password: str) -> User:
    return create_user(
        test_db_session,
        email=email,
        password=password,
        role=UserRole.ADMIN,
    )


def _login_headers(email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    client.cookies.clear()
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
        test_db_session=test_db_session,
    )
    _register_user(
        email="student_target@cola-zero.edu",
        password="student-target-pass",
        role="student",
        student_code="24680",
        test_db_session=test_db_session,
    )
    _register_user(
        email="student_hidden@cola-zero.edu",
        password="student-hidden-pass",
        role="student",
        student_code="13579",
        test_db_session=test_db_session,
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
        test_db_session=test_db_session,
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
        test_db_session=test_db_session,
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
        test_db_session=test_db_session,
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


def test_admin_can_list_users_and_see_inactive_accounts(
    override_get_db,
    test_db_session,
):
    _create_admin_user(
        test_db_session,
        email="admin_list@cola-zero.edu",
        password="admin-list-pass",
    )
    _register_user(
        email="teacher_active@cola-zero.edu",
        password="teacher-active-pass",
        role="teacher",
        test_db_session=test_db_session,
    )
    _register_user(
        email="student_inactive@cola-zero.edu",
        password="student-inactive-pass",
        role="student",
        student_code="77777",
        test_db_session=test_db_session,
    )
    inactive = (
        test_db_session.query(User).filter(User.email == "student_inactive@cola-zero.edu").one()
    )
    inactive.is_active = False
    test_db_session.commit()

    headers = _login_headers("admin_list@cola-zero.edu", "admin-list-pass")
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()

    assert {item["email"] for item in payload} >= {
        "admin_list@cola-zero.edu",
        "teacher_active@cola-zero.edu",
        "student_inactive@cola-zero.edu",
    }
    inactive_item = next(item for item in payload if item["email"] == "student_inactive@cola-zero.edu")
    assert inactive_item["is_active"] is False


def test_admin_can_archive_and_delete_user(override_get_db, test_db_session):
    _create_admin_user(
        test_db_session,
        email="admin_manage@cola-zero.edu",
        password="admin-manage-pass",
    )
    _register_user(
        email="teacher_manage@cola-zero.edu",
        password="teacher-manage-pass",
        role="teacher",
        test_db_session=test_db_session,
    )
    headers = _login_headers("admin_manage@cola-zero.edu", "admin-manage-pass")

    archive_response = client.post(
        "/api/v1/users/{}/archive".format(
            test_db_session.query(User).filter(User.email == "teacher_manage@cola-zero.edu").one().id
        ),
        headers=headers,
    )
    assert archive_response.status_code == 200, archive_response.text
    assert archive_response.json()["is_active"] is False

    delete_response = client.delete(
        "/api/v1/users/{}".format(
            test_db_session.query(User).filter(User.email == "teacher_manage@cola-zero.edu").one().id
        ),
        headers=headers,
    )
    assert delete_response.status_code == 200, delete_response.text
    delete_payload = delete_response.json()
    assert delete_payload["is_active"] is False
    assert delete_payload["email"].startswith("anonymized-")

    target_id = UUID(delete_payload["id"])
    audit_events = (
        test_db_session.query(AuditLog)
        .filter(AuditLog.resource_type == "user", AuditLog.resource_id == target_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    event_types = [event.event_type for event in audit_events]
    assert event_types == [
        "admin.user_archive_requested",
        "admin.user_archived",
        "admin.user_delete_requested",
        "lgpd.anonymization_requested",
        "admin.user_deleted",
    ]

    requested_event = next(event for event in audit_events if event.event_type == "admin.user_delete_requested")
    assert requested_event.details["email"] == "teacher_manage@cola-zero.edu"
    assert requested_event.details["previous_is_active"] is False

    deleted_event = next(event for event in audit_events if event.event_type == "admin.user_deleted")
    assert deleted_event.details["email"].startswith("anonymized-")
    assert deleted_event.details["is_active"] is False
