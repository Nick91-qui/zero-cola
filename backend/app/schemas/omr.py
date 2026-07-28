from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import GradeSourceType, OMRScanStatus

# --- OMR Template Schemas ---


class OMRTemplateBase(BaseModel):
    exam_id: Optional[UUID] = None
    layout_version: str
    total_questions: int
    options_per_question: int = 5


class OMRTemplateCreate(OMRTemplateBase):
    correct_answers: Optional[Dict[str, str]] = None


class OMRTemplateResponse(OMRTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- OMR Scan Schemas ---


class OMRScanBase(BaseModel):
    omr_template_id: UUID
    student_code: Optional[str] = None
    student_id: Optional[UUID] = None
    status: OMRScanStatus
    image_url: str
    detected_answers: Optional[Dict[str, Optional[str]]] = None
    raw_confidence: Optional[Dict[str, Any]] = None
    score: Optional[Decimal] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


class OMRScanResponse(OMRScanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OMRScanUpdate(BaseModel):
    student_code: Optional[str] = None
    detected_answers: Optional[Dict[str, Optional[str]]] = None
    status: Optional[OMRScanStatus] = None


# --- Grade Schemas ---


class GradeBase(BaseModel):
    student_id: UUID
    source_type: GradeSourceType
    source_id: UUID
    score: Decimal
    teacher_id: UUID


class GradeCreate(GradeBase):
    pass


class GradeResponse(GradeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
