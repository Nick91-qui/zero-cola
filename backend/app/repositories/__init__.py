from app.repositories.grade import GradeRepository
from app.repositories.omr import OMRScanRepository, OMRTemplateRepository
from app.repositories.user import UserRepository

__all__ = ["UserRepository", "OMRTemplateRepository", "OMRScanRepository", "GradeRepository"]
