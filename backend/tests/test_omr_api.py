import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from tests.test_omr_service import create_synthetic_sheet_bytes

client = TestClient(app)


@pytest.fixture
def auth_headers(test_db_session):
    """Creates a teacher user and returns authorization headers."""
    service = AuthService(test_db_session)
    user_create = type(
        "UserCreate",
        (),
        {
            "email": "teacher_api@cola-zero.edu",
            "password": "teacherpass123",
            "role": UserRole.TEACHER,
        },
    )()
    password_hash = service.hash_password("teacherpass123")

    repo = UserRepository(test_db_session)
    repo.create(user_create, password_hash)

    # Generate token
    user_login = type(
        "UserLogin",
        (),
        {"email": "teacher_api@cola-zero.edu", "password": "teacherpass123"},
    )()
    token_data = service.authenticate_user(user_login)
    access_token = token_data["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


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


def test_omr_api_workflow(override_get_db, test_db_session, auth_headers, student_user, tmp_path):
    # Set upload dir for testing

    # Override upload_dir in service if needed, or rely on tmp_path indirectly.
    # To be safe, we can mock/configure it or let it use the default local folder.

    # 1. Create Template
    template_data = {
        "layout_version": "v1_std_20q",
        "total_questions": 20,
        "options_per_question": 5,
        "correct_answers": {"1": "A", "2": "B", "3": "C"},
    }

    response = client.post("/api/v1/omr/templates", json=template_data, headers=auth_headers)
    assert response.status_code == 201
    template = response.json()
    template_id = template["id"]
    assert template["layout_version"] == "v1_std_20q"

    # 2. Get PDF
    pdf_response = client.get(
        f"/api/v1/omr/templates/{template_id}/pdf?student_code=77777",
        headers=auth_headers,
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")

    # 3. Create Synthetic Image and Upload
    sheet_bytes = create_synthetic_sheet_bytes(
        student_code="77777", answers={"1": "A", "2": "B", "3": "C"}
    )

    files = {"file": ("scan.png", sheet_bytes, "image/png")}
    data = {"omr_template_id": template_id}

    upload_response = client.post(
        "/api/v1/omr/scans/upload", headers=auth_headers, files=files, data=data
    )
    assert upload_response.status_code == 201
    scan = upload_response.json()
    scan_id = scan["id"]

    assert scan["status"] == "success"
    assert scan["student_code"] == "77777"
    assert scan["student_id"] == str(student_user.id)
    assert float(scan["score"]) == 1.50  # 3 out of 20 correct -> 1.50

    # 4. Get Scan Info
    get_response = client.get(f"/api/v1/omr/scans/{scan_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == scan_id

    # 5. Update Scan Manually
    update_data = {"detected_answers": {"1": "A", "2": "B", "3": "D"}}
    update_response = client.patch(
        f"/api/v1/omr/scans/{scan_id}", json=update_data, headers=auth_headers
    )
    assert update_response.status_code == 200
    updated_scan = update_response.json()
    assert updated_scan["detected_answers"]["3"] == "D"
    assert float(updated_scan["score"]) == 1.00

    # 6. Confirm Scan and Create Grade
    confirm_response = client.post(f"/api/v1/omr/scans/{scan_id}/confirm", headers=auth_headers)
    assert confirm_response.status_code == 200
    grade = confirm_response.json()

    assert grade["student_id"] == str(student_user.id)
    assert float(grade["score"]) == 1.00
    assert grade["source_type"] == "OMR"
    assert grade["source_id"] == scan_id


def test_omr_list_and_preview(override_get_db, test_db_session, auth_headers):
    template_data = {
        "layout_version": "v1_std_20q",
        "total_questions": 20,
        "options_per_question": 5,
        "correct_answers": {"1": "A"},
    }
    created = client.post("/api/v1/omr/templates", json=template_data, headers=auth_headers)
    assert created.status_code == 201
    template_id = created.json()["id"]

    listed = client.get("/api/v1/omr/templates", headers=auth_headers)
    assert listed.status_code == 200
    assert any(item["id"] == template_id for item in listed.json())

    preview = client.get(
        f"/api/v1/omr/templates/{template_id}/preview.png?student_code=77777",
        headers=auth_headers,
    )
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_omr_api_unauthorized(override_get_db):
    # Calling endpoints without auth headers should return 401
    response = client.post("/api/v1/omr/templates", json={})
    assert response.status_code == 401
