from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel
from app.models.enums import AttemptStatus


class Attempt(BaseModel):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint(
            "source IN ('OMR', 'ONLINE')",
            name="ck_attempts_source_valid",
        ),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'submitted', 'graded')",
            name="ck_attempts_status_valid",
        ),
    )

    exam_id: Mapped[UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer_key_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("answer_keys.id", ondelete="RESTRICT"),
        nullable=True,
    )
    student_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_code: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    omr_scan_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("omr_scans.id", ondelete="SET NULL"),
        nullable=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AttemptStatus.NOT_STARTED.value,
        server_default=AttemptStatus.NOT_STARTED.value,
    )
    source: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="OMR",
        server_default="OMR",
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incorrect_answers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accuracy_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    raw_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    final_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    exam = relationship("Exam", back_populates="attempts")
    answer_key = relationship("AnswerKey", foreign_keys=[answer_key_id])
    student = relationship("User", foreign_keys=[student_id])
    omr_scan = relationship("OMRScan", foreign_keys=[omr_scan_id])
    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


class AttemptAnswer(BaseModel):
    __tablename__ = "attempt_answers"

    attempt_id: Mapped[UUID] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_key_item_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("answer_key_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    question_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    selected_option: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    correct_option: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt = relationship("Attempt", back_populates="answers")
    answer_key_item = relationship("AnswerKeyItem", foreign_keys=[answer_key_item_id])
    question = relationship("Question", foreign_keys=[question_id])
