from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.db.base import Base
from app.db.models import BaseModel

# Association table for AnswerKeyItem <-> Skill (direct skill attachment
# without requiring a Question Bank row — supports Workflow B).
answer_key_item_skills = Table(
    "answer_key_item_skills",
    Base.metadata,
    Column(
        "answer_key_item_id",
        ForeignKey("answer_key_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id",
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class AnswerKey(BaseModel):
    """Canonical record of correct answers for an Exam.

    Single source of truth for grading, OMR, statistics, dashboard, and exports.
    1:1 with Exam (enforced by UNIQUE constraint on exam_id).
    """

    __tablename__ = "answer_keys"

    exam_id: Mapped[UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    exam = relationship(
        "Exam",
        foreign_keys=[exam_id],
        backref=backref("answer_key", uselist=False),
    )
    items = relationship(
        "AnswerKeyItem",
        back_populates="answer_key",
        cascade="all, delete-orphan",
        order_by="AnswerKeyItem.item_number",
    )


class AnswerKeyItem(BaseModel):
    """One graded slot within an AnswerKey.

    Replaces the answer-key role of the legacy exam-bound `questions` table.
    """

    __tablename__ = "answer_key_items"
    __table_args__ = (
        UniqueConstraint("answer_key_id", "item_number", name="uq_answer_key_item_number"),
    )

    answer_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("answer_keys.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_number: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
        server_default="1.00",
    )
    statement: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    question_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )

    answer_key = relationship("AnswerKey", back_populates="items")
    question = relationship("Question", foreign_keys=[question_id])
    skills = relationship(
        "Skill",
        secondary=answer_key_item_skills,
        backref="answer_key_items",
    )
