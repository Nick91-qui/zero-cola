from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.STUDENT, description="User role")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: UserRole | None = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


__all__ = ["UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserLogin"]
