from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.exam import ExamResponse
from app.schemas.user import UserResponse


class AttemptAnswerResponse(BaseModel):
    id: UUID
    attempt_id: UUID
    question_number: int
    question_id: Optional[UUID] = None
    selected_option: Optional[str] = None
    correct_option: Optional[str] = None
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


class AttemptResponse(BaseModel):
    id: UUID
    exam_id: UUID
    student_id: Optional[UUID] = None
    student_code: Optional[str] = None
    omr_scan_id: Optional[UUID] = None
    status: str
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    accuracy_percentage: Decimal
    raw_score: Decimal
    final_score: Decimal
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    exam: Optional[ExamResponse] = None
    student: Optional[UserResponse] = None
    answers: List[AttemptAnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)
