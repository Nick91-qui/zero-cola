from app.repositories.attempt import AttemptRepository
from app.repositories.exam import ExamRepository
from app.repositories.grade import GradeRepository
from app.repositories.omr import OMRScanRepository, OMRTemplateRepository
from app.repositories.skill import SkillRepository
from app.repositories.user import UserRepository

__all__ = [
    "UserRepository",
    "OMRTemplateRepository",
    "OMRScanRepository",
    "GradeRepository",
    "ExamRepository",
    "AttemptRepository",
    "SkillRepository",
]
