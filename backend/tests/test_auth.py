import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService

client = TestClient(app)


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "securepass123",
        "role": "student",
    }


@pytest.fixture
def create_test_user(test_db_session, test_user_data):
    """Create a test user."""
    service = AuthService(test_db_session)
    user_create = type("UserCreate", (), {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
        "role": UserRole.STUDENT,
    })()
    password_hash = service.hash_password(test_user_data["password"])

    repo = UserRepository(test_db_session)
    user = repo.create(user_create, password_hash)
    return user


def test_register_user_success(override_get_db, test_db_session, test_user_data):
    """Test successful user registration."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["role"] == "student"
    assert "id" in data


def test_register_user_duplicate_email(override_get_db, test_db_session, test_user_data, create_test_user):
    """Test registration fails with duplicate email."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


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


def test_get_current_user_no_token(override_get_db):
    """Test get current user fails without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
