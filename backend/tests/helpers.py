from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.schemas import UserCreate
from app.services.auth import AuthService


def create_user(
    test_db_session,
    *,
    email: str,
    password: str,
    role: UserRole,
    student_code: str | None = None,
):
    service = AuthService(test_db_session)
    user_create = UserCreate(
        email=email,
        password=password,
        role=role,
        student_code=student_code,
    )
    password_hash = service.hash_password(password)
    return UserRepository(test_db_session).create(user_create, password_hash)
