from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class ClassBase(BaseModel):
    name: str = Field(..., max_length=255)
    academic_period: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None


class ClassCreate(ClassBase):
    teacher_id: Optional[UUID] = None


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None


class ClassStudentCreate(BaseModel):
    student_ids: list[UUID]


class ClassStudentTransferCreate(BaseModel):
    target_class_id: UUID


class ClassStudentBulkTransferCreate(BaseModel):
    target_class_id: UUID


class ClassTeacherCreate(BaseModel):
    teacher_ids: list[UUID]


class ClassStudentResponse(BaseModel):
    id: UUID
    class_id: UUID
    student_id: UUID
    academic_period: str
    student: Optional[UserResponse] = None
    is_active: bool
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassResponse(ClassBase):
    id: UUID
    teacher_id: UUID | None
    is_active: bool
    archived_at: Optional[datetime] = None
    student_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassTeacherResponse(BaseModel):
    id: UUID
    class_id: UUID
    teacher_id: UUID
    teacher: Optional[UserResponse] = None
    is_active: bool
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassDetailResponse(ClassResponse):
    memberships: list[ClassStudentResponse] = Field(default_factory=list)
    teachers: list[ClassTeacherResponse] = Field(default_factory=list)


class ClassStudentTransferResponse(BaseModel):
    student_id: UUID
    source_class_id: UUID
    target_class_id: UUID
    source_membership: ClassStudentResponse
    target_membership: ClassStudentResponse

    model_config = ConfigDict(from_attributes=True)


class ClassStudentBulkTransferResponse(BaseModel):
    source_class_id: UUID
    target_class_id: UUID
    transferred_count: int
    transfers: list[ClassStudentTransferResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
