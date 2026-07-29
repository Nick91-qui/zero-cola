from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.exam import ExamResponse
from app.schemas.omr import GradeResponse
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


class StudentAttemptAnswerResponse(BaseModel):
    id: UUID
    attempt_id: UUID
    question_number: int
    question_id: Optional[UUID] = None
    selected_option: Optional[str] = None
    is_correct: bool
    answered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OnlineAttemptActiveAnswerResponse(BaseModel):
    id: UUID
    attempt_id: UUID
    question_number: int
    question_id: Optional[UUID] = None
    selected_option: Optional[str] = None
    answered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentAttemptResponse(BaseModel):
    id: UUID
    exam_id: UUID
    student_id: Optional[UUID] = None
    student_code: Optional[str] = None
    omr_scan_id: Optional[UUID] = None
    attempt_number: int
    source: str
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
    answers: List[StudentAttemptAnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OnlineAttemptProgressResponse(BaseModel):
    id: UUID
    exam_id: UUID
    student_id: Optional[UUID] = None
    student_code: Optional[str] = None
    omr_scan_id: Optional[UUID] = None
    attempt_number: int
    source: str
    status: str
    total_questions: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    answers: List[OnlineAttemptActiveAnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OnlineAttemptQuestionResponse(BaseModel):
    question_number: int
    question_id: Optional[UUID] = None
    statement: Optional[str] = None
    options: Optional[dict[str, Any]] = None
    selected_option: Optional[str] = None
    answered_at: Optional[datetime] = None


class OnlineAttemptSessionResponse(BaseModel):
    attempt: OnlineAttemptProgressResponse
    current_question: Optional[OnlineAttemptQuestionResponse] = None
    total_questions: int


class OnlineAttemptStartRequest(BaseModel):
    exam_id: UUID


class OnlineAttemptAnswerInput(BaseModel):
    selected_option: Optional[str] = None


class OnlineAttemptResultResponse(BaseModel):
    attempt: StudentAttemptResponse
    grade: Optional[GradeResponse] = None
