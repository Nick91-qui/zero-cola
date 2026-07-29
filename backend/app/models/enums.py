from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class OMRScanStatus(str, Enum):
    PROCESSING = "processing"
    SUCCESS = "success"
    REVIEW_NEEDED = "review_needed"
    FAILED = "failed"


class GradeSourceType(str, Enum):
    ONLINE = "ONLINE"
    OMR = "OMR"


class ExamStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
