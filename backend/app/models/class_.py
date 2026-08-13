from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class Class(BaseModel):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("name", "academic_period", name="uq_classes_name_period"),
        Index("ix_classes_teacher_id", "teacher_id"),
        Index("ix_classes_academic_period", "academic_period"),
        Index("ix_classes_is_active", "is_active"),
    )

    teacher_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_period: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    teacher = relationship("User", foreign_keys=[teacher_id], backref="created_classes")
    teacher_links = relationship(
        "TeacherClass",
        back_populates="class_",
        cascade="all, delete-orphan",
    )
    memberships = relationship(
        "ClassStudent",
        back_populates="class_",
        cascade="all, delete-orphan",
    )

    @property
    def student_count(self) -> int:
        return sum(1 for membership in self.memberships if membership.is_active)

    @property
    def teacher_count(self) -> int:
        return sum(1 for link in self.teacher_links if link.is_active)


class ClassStudent(BaseModel):
    __tablename__ = "class_students"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_students_class_student"),
        Index("ix_class_students_class_id", "class_id"),
        Index("ix_class_students_student_id", "student_id"),
        Index("ix_class_students_academic_period", "academic_period"),
        Index("ix_class_students_is_active", "is_active"),
        Index(
            "ix_class_students_student_period_active",
            "student_id",
            "academic_period",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active = true"),
        ),
    )

    class_id: Mapped[UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_period: Mapped[str] = mapped_column(String(20), nullable=False)
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

    class_ = relationship("Class", back_populates="memberships")
    student = relationship("User", foreign_keys=[student_id], backref="class_memberships")


class TeacherClass(BaseModel):
    __tablename__ = "teacher_classes"
    __table_args__ = (
        UniqueConstraint("teacher_id", "class_id", name="uq_teacher_classes_teacher_class"),
        Index("ix_teacher_classes_teacher_id", "teacher_id"),
        Index("ix_teacher_classes_class_id", "class_id"),
        Index("ix_teacher_classes_is_active", "is_active"),
    )

    teacher_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    class_id: Mapped[UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
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

    teacher = relationship("User", foreign_keys=[teacher_id], backref="teaching_classes")
    class_ = relationship("Class", back_populates="teacher_links")
