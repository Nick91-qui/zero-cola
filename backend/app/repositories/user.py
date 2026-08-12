from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.schemas import UserCreate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_create: UserCreate, password_hash: str) -> User:
        db_user = User(
            email=user_create.email,
            password_hash=password_hash,
            role=user_create.role,
            student_code=getattr(user_create, "student_code", None),
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_student_code(self, student_code: str) -> User | None:
        return self.db.query(User).filter(User.student_code == student_code).first()

    def get_by_id(self, user_id: str | UUID) -> User | None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def list_users(
        self,
        *,
        query: str = "",
        role: UserRole | None = None,
        include_inactive: bool = True,
        limit: int = 100,
        skip: int = 0,
    ) -> list[User]:
        normalized = query.strip()
        safe_limit = max(1, min(limit, 100))
        safe_skip = max(0, skip)

        user_query = self.db.query(User)
        if not include_inactive:
            user_query = user_query.filter(
                User.is_active.is_(True),
                User.anonymized_at.is_(None),
            )
        if role is not None:
            user_query = user_query.filter(User.role == role)

        if normalized:
            pattern = f"%{normalized}%"
            filters = [User.email.ilike(pattern)]
            if normalized.isdigit():
                filters.append(User.student_code.ilike(pattern))
            user_query = user_query.filter(or_(*filters))

        return (
            user_query.order_by(User.role.asc(), User.email.asc())
            .offset(safe_skip)
            .limit(safe_limit)
            .all()
        )

    def search(
        self,
        *,
        query: str,
        role: UserRole | None = None,
        limit: int = 10,
    ) -> list[User]:
        normalized = query.strip()
        if not normalized:
            return []

        safe_limit = max(1, min(limit, 20))
        pattern = f"%{normalized}%"

        search_query = self.db.query(User).filter(
            User.is_active.is_(True),
            User.anonymized_at.is_(None),
        )
        if role is not None:
            search_query = search_query.filter(User.role == role)

        filters = [User.email.ilike(pattern)]
        if normalized.isdigit():
            filters.append(User.student_code.ilike(pattern))

        return (
            search_query.filter(or_(*filters))
            .order_by(User.email.asc())
            .limit(safe_limit)
            .all()
        )

    def update(self, user_id: str | UUID, **kwargs) -> User | None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        user = self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user

    def delete(self, user_id: str | UUID) -> bool:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
