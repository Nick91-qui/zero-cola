from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel
from app.models.enums import OMRScanStatus


class OMRTemplate(BaseModel):
    __tablename__ = "omr_templates"

    # exam_id is a logical reference until the exams table exists.
    exam_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    layout_version: Mapped[str] = mapped_column(String(50), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    options_per_question: Mapped[int] = mapped_column(
        Integer,
        default=5,
        server_default="5",
        nullable=False,
    )
    correct_answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class OMRScan(BaseModel):
    __tablename__ = "omr_scans"

    omr_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("omr_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_code: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    student_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[OMRScanStatus] = mapped_column(
        SQLEnum(
            OMRScanStatus,
            name="omr_scan_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=OMRScanStatus.PROCESSING,
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    detected_answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_confidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    omr_template = relationship("OMRTemplate", backref="scans")
    student = relationship("User", foreign_keys=[student_id])
