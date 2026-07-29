from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class ExamQuestion(BaseModel):
    """Composition join between a bank Question and an Exam.

    Exists only in Workflow A. At publication time, ExamQuestions are
    projected into AnswerKeyItems. Grading does not use ExamQuestion.
    """

    __tablename__ = "exam_questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", name="uq_exam_question"),
        UniqueConstraint("exam_id", "display_order", name="uq_exam_question_order"),
    )

    exam_id: Mapped[UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")
