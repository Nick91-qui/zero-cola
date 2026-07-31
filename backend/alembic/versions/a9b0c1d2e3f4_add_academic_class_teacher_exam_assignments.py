"""add academic class, teacher and exam assignment support

Revision ID: a9b0c1d2e3f4
Revises: f7a8b9c0d1e2
Create Date: 2026-07-31 00:00:00.000000

Step 9+ — Academic model hardening.

Adds the academic period to classes and class_students, introduces the
teacher_classes association for many-to-many teacher access, and introduces
exam_classes for many-to-many exam assignment.
"""

from typing import Sequence, Union
from uuid import UUID, uuid4

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    op.add_column(
        "classes",
        sa.Column("academic_period", sa.String(length=20), nullable=True),
    )
    if dialect_name == "sqlite":
        op.execute(
            sa.text(
                """
                UPDATE classes
                SET academic_period = COALESCE(
                    academic_period,
                    CAST(strftime('%Y', created_at) AS TEXT)
                )
                """
            )
        )
    else:
        op.execute(
            sa.text(
                """
                UPDATE classes
                SET academic_period = COALESCE(
                    academic_period,
                    CAST(EXTRACT(YEAR FROM created_at) AS TEXT)
                )
                """
            )
        )
    op.alter_column(
        "classes",
        "academic_period",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.drop_constraint("uq_classes_teacher_name", "classes", type_="unique")
    op.create_unique_constraint(
        "uq_classes_name_period",
        "classes",
        ["name", "academic_period"],
    )
    op.create_index("ix_classes_academic_period", "classes", ["academic_period"])

    op.add_column(
        "class_students",
        sa.Column("academic_period", sa.String(length=20), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE class_students
            SET academic_period = (
                SELECT c.academic_period
                FROM classes c
                WHERE c.id = class_students.class_id
            )
            """
        )
    )
    op.alter_column(
        "class_students",
        "academic_period",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.drop_constraint(
        "fk_class_students_student_id_users",
        "class_students",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_class_students_student_id_users",
        "class_students",
        "users",
        ["student_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_class_students_academic_period",
        "class_students",
        ["academic_period"],
    )
    op.create_index(
        "ix_class_students_student_period_active",
        "class_students",
        ["student_id", "academic_period"],
        unique=True,
        sqlite_where=sa.text("is_active = 1"),
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "teacher_classes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            name="fk_teacher_classes_teacher_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["class_id"],
            ["classes.id"],
            name="fk_teacher_classes_class_id_classes",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "class_id", name="uq_teacher_classes_teacher_class"),
    )
    op.create_index("ix_teacher_classes_teacher_id", "teacher_classes", ["teacher_id"])
    op.create_index("ix_teacher_classes_class_id", "teacher_classes", ["class_id"])
    op.create_index("ix_teacher_classes_is_active", "teacher_classes", ["is_active"])

    class_rows = bind.execute(
        sa.text(
            """
            SELECT id, teacher_id, created_at, updated_at
            FROM classes
            ORDER BY created_at ASC
            """
        )
    ).mappings().all()
    teacher_class_rows = [
        {
            "id": uuid4(),
            "teacher_id": row["teacher_id"],
            "class_id": row["id"],
            "is_active": True,
            "archived_at": None,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in class_rows
    ]
    if teacher_class_rows:
        op.bulk_insert(
            sa.table(
                "teacher_classes",
                sa.column("id", sa.UUID()),
                sa.column("teacher_id", sa.UUID()),
                sa.column("class_id", sa.UUID()),
                sa.column("is_active", sa.Boolean()),
                sa.column("archived_at", sa.DateTime(timezone=True)),
                sa.column("created_at", sa.DateTime(timezone=True)),
                sa.column("updated_at", sa.DateTime(timezone=True)),
            ),
            teacher_class_rows,
        )

    op.create_table(
        "exam_classes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("class_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["exam_id"],
            ["exams.id"],
            name="fk_exam_classes_exam_id_exams",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["class_id"],
            ["classes.id"],
            name="fk_exam_classes_class_id_classes",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "class_id", name="uq_exam_classes_exam_class"),
    )
    op.create_index("ix_exam_classes_exam_id", "exam_classes", ["exam_id"])
    op.create_index("ix_exam_classes_class_id", "exam_classes", ["class_id"])
    op.create_index("ix_exam_classes_is_active", "exam_classes", ["is_active"])

    exam_rows = bind.execute(
        sa.text(
            """
            SELECT id, class_id, created_at, updated_at
            FROM exams
            WHERE class_id IS NOT NULL AND class_id <> ''
            ORDER BY created_at ASC
            """
        )
    ).mappings().all()
    class_ids_by_text = {
        str(row["id"]): row["id"]
        for row in bind.execute(sa.text("SELECT id FROM classes")).mappings().all()
    }
    exam_class_rows = []
    for row in exam_rows:
        try:
            class_uuid = UUID(str(row["class_id"]))
        except (TypeError, ValueError):
            continue

        class_id = class_ids_by_text.get(str(class_uuid))
        if class_id is None:
            continue

        exam_class_rows.append(
            {
                "id": uuid4(),
                "exam_id": row["id"],
                "class_id": class_id,
                "is_active": True,
                "archived_at": None,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    if exam_class_rows:
        op.bulk_insert(
            sa.table(
                "exam_classes",
                sa.column("id", sa.UUID()),
                sa.column("exam_id", sa.UUID()),
                sa.column("class_id", sa.UUID()),
                sa.column("is_active", sa.Boolean()),
                sa.column("archived_at", sa.DateTime(timezone=True)),
                sa.column("created_at", sa.DateTime(timezone=True)),
                sa.column("updated_at", sa.DateTime(timezone=True)),
            ),
            exam_class_rows,
        )


def downgrade() -> None:
    op.drop_index("ix_exam_classes_is_active", table_name="exam_classes")
    op.drop_index("ix_exam_classes_class_id", table_name="exam_classes")
    op.drop_index("ix_exam_classes_exam_id", table_name="exam_classes")
    op.drop_table("exam_classes")

    op.drop_index("ix_teacher_classes_is_active", table_name="teacher_classes")
    op.drop_index("ix_teacher_classes_class_id", table_name="teacher_classes")
    op.drop_index("ix_teacher_classes_teacher_id", table_name="teacher_classes")
    op.drop_table("teacher_classes")

    op.drop_index(
        "ix_class_students_student_period_active",
        table_name="class_students",
    )
    op.drop_index("ix_class_students_academic_period", table_name="class_students")
    op.drop_constraint(
        "fk_class_students_student_id_users",
        "class_students",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_class_students_student_id_users",
        "class_students",
        "users",
        ["student_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("class_students", "academic_period")

    op.drop_index("ix_classes_academic_period", table_name="classes")
    op.drop_constraint("uq_classes_name_period", "classes", type_="unique")
    op.create_unique_constraint(
        "uq_classes_teacher_name",
        "classes",
        ["teacher_id", "name"],
    )
    op.drop_column("classes", "academic_period")
