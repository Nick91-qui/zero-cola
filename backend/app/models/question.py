from typing import Any, Optional
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class Question(BaseModel):
    """Reusable Question Bank entry.

    Legacy exam-bound question rows are preserved separately in
    `questions_legacy` by the Step 5 migration.
    """

    __tablename__ = "questions"

    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="multiple_choice")
    options: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(
        JSON().with_variant(postgresql.ARRAY(Text), "postgresql"),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    parent = relationship("Question", remote_side=lambda: [Question.id], backref="versions")
    created_by_user = relationship("User", foreign_keys=[created_by], backref="created_questions")
    skills = relationship("Skill", secondary="question_skills", back_populates="questions")
    exam_questions = relationship("ExamQuestion", back_populates="question")
