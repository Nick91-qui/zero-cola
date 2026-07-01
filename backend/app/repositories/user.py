from uuid import UUID

from sqlalchemy.orm import Session

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
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: str | UUID) -> User | None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

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
