from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class Exam(BaseModel):
    __tablename__ = "exams"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    teacher_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    class_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    omr_template_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("omr_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher = relationship("User", foreign_keys=[teacher_id], backref="created_exams")
    omr_template = relationship("OMRTemplate", foreign_keys=[omr_template_id], backref="exams")
    exam_questions = relationship(
        "ExamQuestion",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="ExamQuestion.display_order",
    )
    questions = association_proxy("exam_questions", "question")
    attempts = relationship("Attempt", back_populates="exam", cascade="all, delete-orphan")
