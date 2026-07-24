from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class Question(BaseModel):
    __tablename__ = "questions"

    exam_id: Mapped[UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    statement: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    correct_option: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("1.00"))

    exam = relationship("Exam", back_populates="questions")
    skills = relationship("Skill", secondary="question_skills", back_populates="questions")
