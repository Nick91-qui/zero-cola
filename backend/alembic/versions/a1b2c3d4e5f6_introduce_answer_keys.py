"""introduce answer_keys, answer_key_items, answer_key_item_skills, exam_questions

Revision ID: a1b2c3d4e5f6
Revises: 9a8f7b6c5d4e
Create Date: 2026-07-27 16:00:00.000000

Step 1 — AnswerKey Foundation (Phase 0 plan).

This migration is ADDITIVE ONLY. It creates four new tables and backfills them
from existing legacy sources (questions + omr_templates.correct_answers).
No existing application behavior is changed. All legacy read/write paths
continue to operate.

Backfill strategy (addresses Phase 0 issues P-01 and P-03):

1. For each OMRTemplate that has `correct_answers` but no Exam (orphan template):
   - Materialize an Exam (title, teacher_id inferred, omr_template_id, etc.)
   - Set template.exam_id to the new Exam
   - Create an AnswerKey for the Exam
   - Create AnswerKeyItems from the template's correct_answers dict

2. For each Exam that already has an OMRTemplate with `correct_answers`:
   - Create an AnswerKey if none exists
   - Create AnswerKeyItems from COALESCE(template.correct_answers, questions)
     The OMR template source is preferred (it was the grading truth).

3. For each Exam with legacy `questions` rows but no OMRTemplate (or template
   without correct_answers):
   - Create an AnswerKey if none exists
   - Create AnswerKeyItems from the questions rows

4. Set AnswerKey.is_published = TRUE for any Exam that has existing graded
   Attempts (the key was effectively in use).

teacher_id inference for orphan templates:
   The migration selects the first active TEACHER user. If none exists,
   it selects the first active ADMIN user. If neither exists, the orphan
   template's Exam is created with a NULL teacher_id override (the column
   is NOT NULL, so this will fail — the migration aborts with a clear error).
   This is a data-quality guard, not a silent failure.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9a8f7b6c5d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. Create answer_keys table ---
    op.create_table(
        "answer_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", name="uq_answer_keys_exam_id"),
    )

    # --- 2. Create answer_key_items table ---
    op.create_table(
        "answer_key_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer_key_id", sa.UUID(), nullable=False),
        sa.Column("item_number", sa.Integer(), nullable=False),
        sa.Column("correct_answer", sa.String(length=50), nullable=False),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), server_default="1.00", nullable=False),
        sa.Column("statement", sa.String(), nullable=True),
        sa.Column("question_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["answer_key_id"], ["answer_keys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("answer_key_id", "item_number", name="uq_answer_key_item_number"),
    )

    # --- 3. Create answer_key_item_skills association table ---
    op.create_table(
        "answer_key_item_skills",
        sa.Column("answer_key_item_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_key_item_id"], ["answer_key_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("answer_key_item_id", "skill_id"),
    )

    # --- 4. Create exam_questions table ---
    op.create_table(
        "exam_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("exam_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=5, scale=2), nullable=False),
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
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "question_id", name="uq_exam_question"),
    )

    # --- 5. Backfill data ---
    _backfill_answer_keys()


def _backfill_answer_keys() -> None:
    """Backfill AnswerKey + AnswerKeyItem from legacy sources.

    Handles four scenarios (Phase 0 issues P-01, P-03):
      A. Orphan OMR template (correct_answers exists, exam_id is NULL)
      B. Exam with OMR template that has correct_answers
      C. Exam with legacy questions but no OMR template (or template without correct_answers)
      D. Set is_published=TRUE for keys belonging to exams with graded attempts
    """
    import uuid
    from datetime import datetime, timezone

    bind = op.get_bind()

    # --- 5a. Resolve a teacher_id for orphan template materialization ---
    teacher_row = bind.execute(
        sa.text(
            "SELECT id FROM users WHERE role = 'teacher' AND is_active = true "
            "ORDER BY created_at LIMIT 1"
        )
    ).fetchone()

    if teacher_row is None:
        teacher_row = bind.execute(
            sa.text(
                "SELECT id FROM users WHERE role = 'admin' AND is_active = true "
                "ORDER BY created_at LIMIT 1"
            )
        ).fetchone()

    if teacher_row is None:
        # If there are no orphan templates, we can skip this entirely
        orphan_count = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM omr_templates "
                "WHERE correct_answers IS NOT NULL AND exam_id IS NULL"
            )
        ).scalar()
        if orphan_count > 0:
            raise RuntimeError(
                f"Cannot materialize {orphan_count} orphan OMR template(s): "
                "no active TEACHER or ADMIN user found to assign as teacher_id. "
                "Please create a teacher user and re-run the migration."
            )
        default_teacher_id = None
    else:
        default_teacher_id = teacher_row[0]

    now = datetime.now(timezone.utc)

    # --- 5b. Scenario A: Orphan OMR templates (correct_answers exists, exam_id is NULL) ---
    orphan_templates = bind.execute(
        sa.text(
            "SELECT id, title, layout_version, total_questions, correct_answers "
            "FROM omr_templates "
            "WHERE correct_answers IS NOT NULL AND exam_id IS NULL"
        )
    ).fetchall()

    for tmpl_row in orphan_templates:
        tmpl_id = tmpl_row[0]
        tmpl_title = tmpl_row[1] or f"Avaliação OMR {tmpl_row[2]}"
        layout_ver = tmpl_row[2]
        total_q = tmpl_row[3]
        correct_answers = tmpl_row[4]  # JSON dict

        if not correct_answers:
            continue

        new_exam_id = uuid.uuid4()
        new_ak_id = uuid.uuid4()

        # Create Exam
        bind.execute(
            sa.text(
                "INSERT INTO exams (id, title, teacher_id, class_id, omr_template_id, "
                "total_questions, max_score, is_active, created_at, updated_at) "
                "VALUES (:id, :title, :teacher_id, NULL, :omr_template_id, "
                ":total_questions, 10.00, true, :now, :now)"
            ),
            {
                "id": str(new_exam_id),
                "title": tmpl_title,
                "teacher_id": str(default_teacher_id),
                "omr_template_id": str(tmpl_id),
                "total_questions": total_q,
                "now": now,
            },
        )

        # Link template to exam
        bind.execute(
            sa.text("UPDATE omr_templates SET exam_id = :exam_id WHERE id = :tmpl_id"),
            {"exam_id": str(new_exam_id), "tmpl_id": str(tmpl_id)},
        )

        # Create AnswerKey
        _create_answer_key_with_items(
            bind,
            answer_key_id=new_ak_id,
            exam_id=new_exam_id,
            correct_answers=correct_answers,
            total_questions=total_q,
            now=now,
        )

    # --- 5c. Scenario B: Exams with OMR template that has correct_answers ---
    # (template.exam_id is NOT NULL, template has correct_answers, exam has no answer_key yet)
    exams_with_omr = bind.execute(
        sa.text(
            "SELECT e.id, e.total_questions, t.correct_answers "
            "FROM exams e "
            "JOIN omr_templates t ON t.exam_id = e.id "
            "WHERE t.correct_answers IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM answer_keys ak WHERE ak.exam_id = e.id)"
        )
    ).fetchall()

    processed_exam_ids = set()

    for exam_row in exams_with_omr:
        exam_id = exam_row[0]
        total_q = exam_row[1]
        correct_answers = exam_row[2]

        if not correct_answers:
            continue

        if exam_id in processed_exam_ids:
            continue

        processed_exam_ids.add(exam_id)

        new_ak_id = uuid.uuid4()
        _create_answer_key_with_items(
            bind,
            answer_key_id=new_ak_id,
            exam_id=exam_id,
            correct_answers=correct_answers,
            total_questions=total_q,
            now=now,
        )

    # --- 5d. Scenario C: Exams with legacy questions but no AnswerKey yet ---
    # These may or may not have an OMR template. If they do but the template has no
    # correct_answers, we fall back to questions.correct_option.
    exams_with_questions = bind.execute(
        sa.text(
            "SELECT e.id, e.omr_template_id "
            "FROM exams e "
            "WHERE EXISTS (SELECT 1 FROM questions q WHERE q.exam_id = e.id) "
            "AND NOT EXISTS (SELECT 1 FROM answer_keys ak WHERE ak.exam_id = e.id)"
        )
    ).fetchall()

    for exam_row in exams_with_questions:
        exam_id = exam_row[0]
        omr_template_id = exam_row[1]

        # Try to get correct_answers from the OMR template if it exists
        template_correct = None
        if omr_template_id is not None:
            tmpl_result = bind.execute(
                sa.text(
                    "SELECT correct_answers FROM omr_templates WHERE id = :tmpl_id"
                ),
                {"tmpl_id": str(omr_template_id)},
            ).fetchone()
            if tmpl_result and tmpl_result[0]:
                template_correct = tmpl_result[0]

        # Get legacy questions for this exam
        questions = bind.execute(
            sa.text(
                "SELECT question_number, correct_option, weight, statement "
                "FROM questions WHERE exam_id = :exam_id "
                "ORDER BY question_number"
            ),
            {"exam_id": str(exam_id)},
        ).fetchall()

        if not questions:
            continue

        new_ak_id = uuid.uuid4()

        # Create AnswerKey
        bind.execute(
            sa.text(
                "INSERT INTO answer_keys (id, exam_id, is_published, published_at, "
                "created_at, updated_at) "
                "VALUES (:id, :exam_id, false, NULL, :now, :now)"
            ),
            {"id": str(new_ak_id), "exam_id": str(exam_id), "now": now},
        )

        # Create AnswerKeyItems
        for q_row in questions:
            q_number = q_row[0]
            q_correct = q_row[1]
            q_weight = q_row[2]
            q_statement = q_row[3]

            # COALESCE: prefer OMR template answer, fall back to question's correct_option
            correct_answer = None
            if template_correct:
                # Try both str(q_number) and "q{q_number}" keys (defensive)
                correct_answer = template_correct.get(str(q_number))
                if correct_answer is None:
                    correct_answer = template_correct.get(f"q{q_number}")

            if correct_answer is None:
                correct_answer = q_correct

            if correct_answer is None:
                # Skip items with no determinable correct answer
                continue

            item_id = uuid.uuid4()
            bind.execute(
                sa.text(
                    "INSERT INTO answer_key_items "
                    "(id, answer_key_id, item_number, correct_answer, weight, "
                    "statement, question_id, created_at, updated_at) "
                    "VALUES (:id, :ak_id, :item_number, :correct_answer, :weight, "
                    ":statement, NULL, :now, :now)"
                ),
                {
                    "id": str(item_id),
                    "ak_id": str(new_ak_id),
                    "item_number": q_number,
                    "correct_answer": correct_answer,
                    "weight": str(q_weight) if q_weight else "1.00",
                    "statement": q_statement,
                    "now": now,
                },
            )

    # --- 5e. Scenario D: Set is_published=TRUE for exams with graded attempts ---
    bind.execute(
        sa.text(
            "UPDATE answer_keys SET is_published = true, published_at = :now "
            "WHERE exam_id IN (SELECT DISTINCT exam_id FROM attempts WHERE status = 'graded')"
        ),
        {"now": now},
    )


def _create_answer_key_with_items(
    bind,
    answer_key_id,
    exam_id,
    correct_answers,
    total_questions,
    now,
):
    """Create an AnswerKey and its items from a correct_answers dict."""
    if not correct_answers:
        return

    import uuid

    # Create AnswerKey
    bind.execute(
        sa.text(
            "INSERT INTO answer_keys (id, exam_id, is_published, published_at, "
            "created_at, updated_at) "
            "VALUES (:id, :exam_id, false, NULL, :now, :now)"
        ),
        {"id": str(answer_key_id), "exam_id": str(exam_id), "now": now},
    )

    # Create AnswerKeyItems from the correct_answers dict
    # Keys may be "1", "2", ... or "q1", "q2", ... — handle both
    if correct_answers:
        for key, value in correct_answers.items():
            if value is None:
                continue

            # Parse item_number from key
            try:
                item_number = int(str(key).replace("q", "").replace("Q", ""))
            except (ValueError, TypeError):
                continue

            item_id = uuid.uuid4()
            bind.execute(
                sa.text(
                    "INSERT INTO answer_key_items "
                    "(id, answer_key_id, item_number, correct_answer, weight, "
                    "statement, question_id, created_at, updated_at) "
                    "VALUES (:id, :ak_id, :item_number, :correct_answer, 1.00, "
                    "NULL, NULL, :now, :now)"
                ),
                {
                    "id": str(item_id),
                    "ak_id": str(answer_key_id),
                    "item_number": item_number,
                    "correct_answer": str(value),
                    "now": now,
                },
            )


def downgrade() -> None:
    op.drop_table("exam_questions")
    op.drop_table("answer_key_item_skills")
    op.drop_table("answer_key_items")
    op.drop_table("answer_keys")

    # Note: Exams materialized for orphan templates during upgrade are NOT
    # automatically removed in downgrade. They are valid Exam records that
    # may have been used. If a clean rollback is needed, the operator must
    # manually identify and remove Exams created by this migration
    # (they can be identified by having an answer_key that no longer exists
    # after downgrade, or by checking the migration's audit trail).
    # The omr_templates.exam_id links set during upgrade will be dangling
    # after downgrade — they should be manually set to NULL if needed:
    #   UPDATE omr_templates SET exam_id = NULL WHERE exam_id NOT IN (SELECT id FROM exams);
    # However, since the Exams are NOT dropped, the FKs remain valid.
