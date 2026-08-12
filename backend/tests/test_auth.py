import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import UserRole
from tests.helpers import create_user

client = TestClient(app)


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "securepass123",
        "role": "student",
        "student_code": "12345",
    }


@pytest.fixture
def create_test_user(test_db_session, test_user_data):
    """Create a test user."""
    return create_user(
        test_db_session,
        email=test_user_data["email"],
        password=test_user_data["password"],
        role=UserRole.STUDENT,
        student_code=test_user_data["student_code"],
    )


def test_public_registration_endpoint_is_disabled():
    """Public registration must remain disabled."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "blocked@example.com",
            "password": "securepass123",
            "role": "student",
            "student_code": "12345",
        },
    )
    assert response.status_code == 404


def test_login_success(override_get_db, test_db_session, test_user_data, create_test_user):
    """Test successful login."""
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    client.cookies.clear()


def test_login_wrong_password(override_get_db, test_db_session, test_user_data, create_test_user):
    """Test login fails with wrong password."""
    login_data = {
        "email": test_user_data["email"],
        "password": "wrongpassword",
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_refresh_token(override_get_db, test_db_session, test_user_data, create_test_user):
    """Test token refresh."""
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    refresh_token = login_response.json()["refresh_token"]

    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    client.cookies.clear()


def test_get_current_user(override_get_db, test_db_session, test_user_data, create_test_user):
    """Test getting current user info."""
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    client.cookies.clear()


def test_get_current_user_no_token(override_get_db):
    """Test get current user fails without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_patch_me_student_code(override_get_db, test_db_session, test_user_data, create_test_user):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    response = client.patch("/api/v1/auth/me", json={"student_code": "99999"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["student_code"] == "99999"
    client.cookies.clear()


def test_get_current_user_works_with_cookie_session(override_get_db, test_db_session, test_user_data, create_test_user):
    cookie_client = TestClient(app)
    login_response = cookie_client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert login_response.status_code == 200

    response = cookie_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == test_user_data["email"]
    cookie_client.cookies.clear()
