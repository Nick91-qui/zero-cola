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


class AttemptStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"


class PrivacyRequestType(str, Enum):
    ANONYMIZATION = "anonymization"


class PrivacyRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
