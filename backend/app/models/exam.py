from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel
from app.models.enums import ExamStatus


class Exam(BaseModel):
    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_exams_status_valid",
        ),
    )

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
    total_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    randomization_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ExamStatus.DRAFT.value,
        server_default=ExamStatus.DRAFT.value,
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
    class_assignments = relationship(
        "ExamClass",
        back_populates="exam",
        cascade="all, delete-orphan",
    )

    @property
    def class_ids(self) -> list[UUID]:
        return [
            assignment.class_id
            for assignment in sorted(
                self.class_assignments,
                key=lambda assignment: assignment.created_at,
            )
            if assignment.is_active
        ]


class ExamClass(BaseModel):
    __tablename__ = "exam_classes"
    __table_args__ = (
        UniqueConstraint("exam_id", "class_id", name="uq_exam_classes_exam_class"),
        Index("ix_exam_classes_exam_id", "exam_id"),
        Index("ix_exam_classes_class_id", "class_id"),
        Index("ix_exam_classes_is_active", "is_active"),
    )

    exam_id: Mapped[UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    exam = relationship("Exam", back_populates="class_assignments")
    class_ = relationship("Class", backref="exam_class_links")
