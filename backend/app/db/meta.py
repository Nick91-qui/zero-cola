from app.db.base import Base
from app.models import Grade, OMRScan, OMRTemplate, User

metadata = Base.metadata

__all__ = ["Base", "User", "OMRTemplate", "OMRScan", "Grade", "metadata"]
