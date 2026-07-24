from decimal import Decimal
from uuid import UUID

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel
from app.models.enums import GradeSourceType


class Grade(BaseModel):
    __tablename__ = "grades"

    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_type: Mapped[GradeSourceType] = mapped_column(
        SQLEnum(
            GradeSourceType,
            name="grade_source_type",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    teacher_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    student = relationship("User", foreign_keys=[student_id], backref="grades")
    teacher = relationship("User", foreign_keys=[teacher_id], backref="graded_assessments")
