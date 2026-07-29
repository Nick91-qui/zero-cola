"""repurpose questions into reusable question bank

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-29 10:00:00.000000

Step 5 — Repurpose Question Table.

Legacy exam-bound question rows are preserved by renaming the existing
questions/question_skills tables to *_legacy. A new reusable Question Bank
schema is then created under the canonical `questions` / `question_skills`
table names.
"""
import json
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    _null_legacy_question_provenance()
    _drop_fks_referencing_questions(bind)

    op.rename_table("questions", "questions_legacy")
    op.rename_table("question_skills", "question_skills_legacy")

    op.create_table(
        "questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False, server_default="multiple_choice"),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("correct_answer", postgresql.JSONB(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(length=100), nullable=True),
        sa.Column("difficulty", sa.String(length=30), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["questions.id"],
            name="fk_questions_parent_id_questions",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_questions_created_by_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_questions_bank"),
    )

    op.create_table(
        "question_skills",
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name="fk_question_skills_question_id_questions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name="fk_question_skills_skill_id_skills",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("question_id", "skill_id", name="pk_question_skills_bank"),
    )

    _materialize_legacy_questions_to_bank(bind)
    op.execute(
        sa.text(
            """
            INSERT INTO question_skills (question_id, skill_id)
            SELECT question_id, skill_id
            FROM question_skills_legacy
            ON CONFLICT DO NOTHING
            """
        )
    )

    _create_question_fks()


def downgrade() -> None:
    op.drop_constraint(
        "fk_question_skills_question_id_questions",
        "question_skills",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_exam_questions_question_id_questions",
        "exam_questions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_answer_key_items_question_id_questions",
        "answer_key_items",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_attempt_answers_question_id_questions",
        "attempt_answers",
        type_="foreignkey",
    )

    bind = op.get_bind()
    _materialize_bank_questions_to_legacy(bind)

    op.drop_table("question_skills")
    op.drop_table("questions")

    op.rename_table("question_skills_legacy", "question_skills")
    op.rename_table("questions_legacy", "questions")

    _create_legacy_question_fks()


def _null_legacy_question_provenance() -> None:
    op.execute(
        sa.text("UPDATE answer_key_items SET question_id = NULL WHERE question_id IS NOT NULL")
    )
    op.execute(
        sa.text("UPDATE attempt_answers SET question_id = NULL WHERE question_id IS NOT NULL")
    )


def _drop_fks_referencing_questions(bind) -> None:
    for table_name in ("answer_key_items", "attempt_answers", "exam_questions", "question_skills"):
        for constraint_name in _fk_constraints_for_table(bind, table_name, "questions"):
            op.drop_constraint(constraint_name, table_name, type_="foreignkey")


def _fk_constraints_for_table(bind, table_name: str, referenced_table: str) -> list[str]:
    rows = bind.execute(
        sa.text(
            """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = :table_name
              AND ccu.table_name = :referenced_table
            """
        ),
        {"table_name": table_name, "referenced_table": referenced_table},
    ).all()
    return [row[0] for row in rows]


def _create_question_fks() -> None:
    op.create_foreign_key(
        "fk_answer_key_items_question_id_questions",
        "answer_key_items",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_attempt_answers_question_id_questions",
        "attempt_answers",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_exam_questions_question_id_questions",
        "exam_questions",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def _create_legacy_question_fks() -> None:
    op.create_foreign_key(
        "question_skills_question_id_fkey",
        "question_skills",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "exam_questions_question_id_fkey",
        "exam_questions",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "answer_key_items_question_id_fkey",
        "answer_key_items",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "attempt_answers_question_id_fkey",
        "attempt_answers",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="SET NULL",
    )


def _materialize_bank_questions_to_legacy(bind) -> None:
    bank_question_rows = bind.execute(
        sa.text(
            """
            SELECT
                q.id AS question_id,
                q.statement,
                q.correct_answer,
                q.created_at,
                q.updated_at,
                eq.exam_id,
                eq.display_order,
                eq.weight AS exam_question_weight,
                (
                    SELECT aki.correct_answer
                    FROM answer_key_items aki
                    JOIN answer_keys ak ON ak.id = aki.answer_key_id
                    WHERE ak.exam_id = eq.exam_id
                      AND aki.item_number = eq.display_order
                    LIMIT 1
                ) AS legacy_correct_option
            FROM exam_questions eq
            JOIN questions q ON q.id = eq.question_id
            ORDER BY eq.exam_id, eq.display_order
            """
        )
    ).mappings().all()

    skill_rows = bind.execute(
        sa.text(
            """
            SELECT qs.question_id, qs.skill_id
            FROM question_skills qs
            ORDER BY qs.question_id, qs.skill_id
            """
        )
    ).mappings().all()

    skill_ids_by_question: dict[str, list[str]] = {}
    for row in skill_rows:
        skill_ids_by_question.setdefault(str(row["question_id"]), []).append(str(row["skill_id"]))

    for row in bank_question_rows:
        legacy_question_id = uuid.uuid4()
        bind.execute(
            sa.text(
                """
                INSERT INTO questions_legacy (
                    id,
                    exam_id,
                    question_number,
                    statement,
                    correct_option,
                    weight,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :exam_id,
                    :question_number,
                    :statement,
                    :correct_option,
                    :weight,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "id": legacy_question_id,
                "exam_id": row["exam_id"],
                "question_number": row["display_order"],
                "statement": row["statement"],
                "correct_option": row["legacy_correct_option"],
                "weight": row["exam_question_weight"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )
        bind.execute(
            sa.text(
                """
                UPDATE exam_questions
                SET question_id = :new_id
                WHERE exam_id = :exam_id
                  AND display_order = :display_order
                  AND question_id = :old_id
                """
            ),
            {
                "new_id": legacy_question_id,
                "old_id": row["question_id"],
                "exam_id": row["exam_id"],
                "display_order": row["display_order"],
            },
        )
        bind.execute(
            sa.text(
                """
                UPDATE answer_key_items
                SET question_id = :new_id
                WHERE answer_key_id IN (
                    SELECT id
                    FROM answer_keys
                    WHERE exam_id = :exam_id
                )
                AND item_number = :display_order
                """
            ),
            {
                "new_id": legacy_question_id,
                "exam_id": row["exam_id"],
                "display_order": row["display_order"],
            },
        )

        for skill_id in skill_ids_by_question.get(str(row["question_id"]), []):
            bind.execute(
                sa.text(
                    """
                    INSERT INTO question_skills_legacy (question_id, skill_id)
                    VALUES (:question_id, :skill_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"question_id": legacy_question_id, "skill_id": skill_id},
            )


def _materialize_legacy_questions_to_bank(bind) -> None:
    legacy_question_rows = bind.execute(
        sa.text(
            """
            SELECT
                q.id AS question_id,
                q.exam_id,
                q.question_number,
                q.statement,
                q.correct_option,
                q.weight,
                q.created_at,
                q.updated_at,
                e.teacher_id,
                COALESCE(
                    (
                        SELECT aki.correct_answer
                        FROM answer_key_items aki
                        JOIN answer_keys ak ON ak.id = aki.answer_key_id
                        WHERE ak.exam_id = q.exam_id
                          AND aki.item_number = q.question_number
                        LIMIT 1
                    ),
                    q.correct_option
                ) AS canonical_correct_answer
            FROM questions_legacy q
            JOIN exams e ON e.id = q.exam_id
            ORDER BY q.exam_id, q.question_number
            """
        )
    ).mappings().all()

    for row in legacy_question_rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO questions (
                    id,
                    parent_id,
                    version,
                    is_active,
                    statement,
                    type,
                    options,
                    correct_answer,
                    explanation,
                    image_url,
                    subject,
                    difficulty,
                    tags,
                    created_by,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    NULL,
                    1,
                    TRUE,
                    :statement,
                    'multiple_choice',
                    NULL,
                    CAST(:correct_answer AS jsonb),
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    :created_by,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "id": row["question_id"],
                "statement": row["statement"],
                "correct_answer": json.dumps(row["canonical_correct_answer"]),
                "created_by": row["teacher_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )
