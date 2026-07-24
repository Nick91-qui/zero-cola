from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models import BaseModel

question_skills = Table(
    "question_skills",
    Base.metadata,
    Column("question_id", ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(BaseModel):
    __tablename__ = "skills"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    grade_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    curriculum: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="BNCC")

    questions = relationship("Question", secondary=question_skills, back_populates="skills")
