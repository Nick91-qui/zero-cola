from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.schemas import UserCreate, UserLogin


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False

    def register_user(self, user_create: UserCreate) -> dict:
        """Register a new user."""
        existing_user = self.user_repo.get_by_email(user_create.email)
        if existing_user:
            raise ValueError("Email already registered")

        password_hash = self.hash_password(user_create.password)
        user = self.user_repo.create(user_create, password_hash)

        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }

    def authenticate_user(self, login: UserLogin) -> dict | None:
        """Authenticate user and return tokens."""
        user = self.user_repo.get_by_email(login.email)
        if not user or not self.verify_password(login.password, user.password_hash):
            return None

        access_token = self.create_access_token(user.id, user.role)
        refresh_token = self.create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role.value,
            },
        }

    def create_access_token(self, user_id, role: UserRole, expires_delta: timedelta | None = None) -> str:
        """Create JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "sub": str(user_id),
            "role": role.value,
            "exp": expire,
            "type": "access",
        }
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        return encoded_jwt

    def create_refresh_token(self, user_id, expires_delta: timedelta | None = None) -> str:
        """Create JWT refresh token."""
        if expires_delta is None:
            expires_delta = timedelta(days=7)

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
        }
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        return encoded_jwt

    def verify_token(self, token: str) -> dict | None:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return payload
        except jwt.InvalidTokenError:
            return None

    def refresh_access_token(self, refresh_token: str) -> dict | None:
        """Refresh access token using refresh token."""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None

        new_access_token = self.create_access_token(user.id, user.role)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }
