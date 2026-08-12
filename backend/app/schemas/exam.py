from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ExamStatus
from app.schemas.skill import SkillResponse


class QuestionBase(BaseModel):
    statement: str
    type: str = "multiple_choice"
    options: Optional[dict[str, Any]] = None
    correct_answer: dict[str, Any] | str
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None


class QuestionCreate(QuestionBase):
    skill_ids: Optional[List[UUID]] = None


class QuestionUpdate(BaseModel):
    statement: Optional[str] = None
    type: Optional[str] = None
    options: Optional[dict[str, Any]] = None
    correct_answer: Optional[dict[str, Any] | str] = None
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None
    skill_ids: Optional[List[UUID]] = None


class QuestionResponse(QuestionBase):
    id: UUID
    parent_id: Optional[UUID] = None
    version: int
    is_active: bool
    created_by: UUID
    skills: List[SkillResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamQuestionBase(BaseModel):
    display_order: int
    weight: Decimal = Decimal("1.00")


class ExamQuestionCreate(ExamQuestionBase):
    question_id: Optional[UUID] = None
    question: Optional[QuestionCreate] = None


class ExamQuestionResponse(ExamQuestionBase):
    id: UUID
    exam_id: UUID
    question_id: UUID
    question: QuestionResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    class_id: Optional[str] = None
    class_ids: Optional[List[UUID]] = None
    omr_template_id: Optional[UUID] = None
    total_questions: int = 20
    total_time_seconds: Optional[int] = None
    max_attempts: int = 1
    randomization_enabled: bool = False
    max_score: Decimal = Decimal("10.00")


class ExamCreate(ExamBase):
    correct_answers: Optional[Dict[str, str]] = None
    layout_version: Optional[str] = None
    questions: Optional[List[ExamQuestionCreate]] = None


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    class_id: Optional[str] = None
    class_ids: Optional[List[UUID]] = None
    total_time_seconds: Optional[int] = None
    max_attempts: Optional[int] = None
    randomization_enabled: Optional[bool] = None
    max_score: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ExamResponse(ExamBase):
    id: UUID
    teacher_id: UUID
    status: ExamStatus
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExamDetailResponse(ExamResponse):
    questions: List[QuestionResponse] = []
    exam_questions: List[ExamQuestionResponse] = []


class QuestionStatistic(BaseModel):
    question_number: int
    statement: Optional[str] = None
    correct_option: Optional[str] = None
    skills: List[SkillResponse] = []
    total_responses: int
    correct_count: int
    incorrect_count: int
    accuracy_percentage: float
    error_percentage: float


class ExamStatisticsResponse(BaseModel):
    exam_id: UUID
    exam_title: str
    total_attempts: int
    class_id: Optional[str] = None
    average_score: float
    max_score: float
    question_statistics: List[QuestionStatistic]
