from app.schemas.attempt import AttemptAnswerResponse, AttemptResponse
from app.schemas.exam import (
    ExamCreate,
    ExamDetailResponse,
    ExamResponse,
    ExamStatisticsResponse,
    ExamUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionStatistic,
)
from app.schemas.omr import (
    GradeCreate,
    GradeResponse,
    OMRScanResponse,
    OMRScanUpdate,
    OMRTemplateCreate,
    OMRTemplateResponse,
)
from app.schemas.skill import SkillCreate, SkillResponse
from app.schemas.user import UserBase, UserCreate, UserLogin, UserResponse, UserUpdate

__all__ = [
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",

    "OMRTemplateCreate",
    "OMRTemplateResponse",
    "OMRScanResponse",
    "OMRScanUpdate",
    "GradeCreate",
    "GradeResponse",
    "ExamCreate",
    "ExamUpdate",
    "ExamResponse",
    "ExamDetailResponse",
    "QuestionCreate",
    "QuestionResponse",
    "QuestionStatistic",
    "ExamStatisticsResponse",
    "AttemptResponse",
    "AttemptAnswerResponse",
    "SkillCreate",
    "SkillResponse",
]
