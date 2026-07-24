from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.STUDENT, description="User role")
    student_code: str | None = Field(
        default=None,
        description="5-digit OMR student code (required for students)",
    )

    @field_validator("student_code")
    @classmethod
    def validate_student_code_format(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.isdigit() or len(value) != 5:
            raise ValueError("student_code must be exactly 5 digits")
        return value


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")

    @model_validator(mode="after")
    def require_student_code_for_students(self) -> "UserCreate":
        if self.role == UserRole.STUDENT and not self.student_code:
            raise ValueError("student_code is required for student accounts")
        if self.role != UserRole.STUDENT:
            self.student_code = None
        return self


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: UserRole | None = None
    student_code: str | None = None

    @field_validator("student_code")
    @classmethod
    def validate_student_code_format(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.isdigit() or len(value) != 5:
            raise ValueError("student_code must be exactly 5 digits")
        return value


class UserResponse(UserBase):
    id: UUID
    is_active: bool

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


__all__ = ["UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserLogin"]
