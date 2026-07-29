"""Backfill logic for AnswerKey foundation (Steps 1-2).

This module contains the same backfill logic as the Alembic migration
`a1b2c3d4e5f6_introduce_answer_keys.py`, extracted as a testable Python
function. The Alembic migration calls the same algorithm via raw SQL;
this module uses SQLAlchemy ORM for testability with the SQLite-based
test suite.

The production migration uses raw SQL for performance and to avoid ORM
session issues inside Alembic. This module exists solely for testing.
"""
import json
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.enums import UserRole
from app.models.exam import Exam
from app.models.user import User


def backfill_answer_keys(session: Session) -> dict:
    """Backfill AnswerKey + AnswerKeyItem from legacy sources.

    Returns a summary dict with counts of what was created.
    """
    now = datetime.now(timezone.utc)
    stats = {
        "orphan_templates_materialized": 0,
        "exams_with_omr_backfilled": 0,
        "exams_with_questions_backfilled": 0,
        "answer_keys_created": 0,
        "answer_key_items_created": 0,
        "keys_marked_published": 0,
    }

    # --- Resolve teacher_id for orphan templates ---
    default_teacher = (
        session.query(User)
        .filter(User.role == UserRole.TEACHER, User.is_active.is_(True))
        .order_by(User.created_at)
        .first()
    )
    if default_teacher is None:
        default_teacher = (
            session.query(User)
            .filter(User.role == UserRole.ADMIN, User.is_active.is_(True))
            .order_by(User.created_at)
            .first()
        )

    # --- Scenario A: Orphan OMR templates (correct_answers exists, exam_id is NULL) ---
    orphan_templates = _load_legacy_omr_templates(session, exam_id_is_null=True)

    if orphan_templates and default_teacher is None:
        raise RuntimeError(
            f"Cannot materialize {len(orphan_templates)} orphan OMR template(s): "
            "no active TEACHER or ADMIN user found."
        )

    for tmpl in orphan_templates:
        tmpl_title = tmpl["title"] or f"Avaliação OMR {tmpl['layout_version']}"

        new_exam = Exam(
            title=tmpl_title,
            teacher_id=default_teacher.id,
            omr_template_id=_uuid_object(tmpl["id"]),
            total_questions=tmpl["total_questions"],
            max_score=10.00,
            is_active=True,
        )
        session.add(new_exam)
        session.flush()

        # Link template to exam
        session.execute(
            sa.text("UPDATE omr_templates SET exam_id = :exam_id WHERE id = :id"),
            {"exam_id": _uuid_param(new_exam.id), "id": _uuid_param(tmpl["id"])},
        )
        session.flush()

        ak = AnswerKey(
            exam_id=new_exam.id,
            is_published=False,
        )
        session.add(ak)
        session.flush()

        _create_items_from_dict(session, ak.id, _coerce_correct_answers(tmpl["correct_answers"]))
        stats["orphan_templates_materialized"] += 1
        stats["answer_keys_created"] += 1

    # --- Scenario B: Exams with OMR template that has correct_answers ---
    existing_answer_key_exam_ids = session.query(AnswerKey.exam_id).all()
    existing_ak_set = {_uuid_object(row[0]) for row in existing_answer_key_exam_ids}

    templates_with_answers = _load_legacy_omr_templates(session, exam_id_is_not_null=True)

    for tmpl in templates_with_answers:
        if tmpl["exam_id"] in existing_ak_set:
            continue

        ak = AnswerKey(exam_id=_uuid_object(tmpl["exam_id"]), is_published=False)
        session.add(ak)
        session.flush()

        _create_items_from_dict(session, ak.id, _coerce_correct_answers(tmpl["correct_answers"]))
        stats["exams_with_omr_backfilled"] += 1
        stats["answer_keys_created"] += 1
        existing_ak_set.add(_uuid_object(tmpl["exam_id"]))

    # --- Scenario C: Exams with legacy questions but no AnswerKey ---
    legacy_questions = _load_legacy_questions(session)
    question_exam_ids = {row["exam_id"] for row in legacy_questions}
    exams_with_questions = session.query(Exam).filter(Exam.id.in_(question_exam_ids)).all()

    for exam in exams_with_questions:
        if exam.id in existing_ak_set:
            continue

        # Get correct_answers from template if available
        template_correct = None
        if exam.omr_template_id is not None:
            tmpl = session.execute(
                sa.text(
                    "SELECT correct_answers FROM omr_templates WHERE id = :tmpl_id"
                ),
                {"tmpl_id": _uuid_param(exam.omr_template_id)},
            ).scalar_one_or_none()
            if tmpl:
                template_correct = _coerce_correct_answers(tmpl)

        questions = [row for row in legacy_questions if row["exam_id"] == exam.id]

        if not questions:
            continue

        ak = AnswerKey(exam_id=exam.id, is_published=False)
        session.add(ak)
        session.flush()

        for q in questions:
            # COALESCE: prefer OMR template, fall back to question
            correct_answer = None
            if template_correct:
                correct_answer = template_correct.get(str(q["question_number"]))
                if correct_answer is None:
                    correct_answer = template_correct.get(f"q{q['question_number']}")

            if correct_answer is None:
                correct_answer = q["correct_option"]

            if correct_answer is None:
                continue

            item = AnswerKeyItem(
                answer_key_id=ak.id,
                item_number=q["question_number"],
                correct_answer=str(correct_answer),
                weight=q["weight"] or 1.00,
                statement=q["statement"],
                question_id=None,
            )
            session.add(item)
            stats["answer_key_items_created"] += 1

        stats["exams_with_questions_backfilled"] += 1
        stats["answer_keys_created"] += 1
        existing_ak_set.add(exam.id)

    # --- Scenario D: Mark published for exams with graded attempts ---
    from app.models.attempt import Attempt

    graded_exam_ids = (
        session.query(Attempt.exam_id)
        .filter(Attempt.status == "graded")
        .distinct()
        .all()
    )
    graded_set = {row[0] for row in graded_exam_ids}

    if graded_set:
        keys_to_publish = (
            session.query(AnswerKey)
            .filter(AnswerKey.exam_id.in_(graded_set))
            .all()
        )
        for ak in keys_to_publish:
            if not ak.is_published:
                ak.is_published = True
                ak.published_at = now
                stats["keys_marked_published"] += 1

    session.commit()
    return stats


def _create_items_from_dict(
    session: Session, answer_key_id, correct_answers: dict
):
    """Create AnswerKeyItems from a correct_answers dict."""
    if not correct_answers:
        return

    for key, value in correct_answers.items():
        if value is None:
            continue

        try:
            item_number = int(str(key).replace("q", "").replace("Q", ""))
        except (ValueError, TypeError):
            continue

        item = AnswerKeyItem(
            answer_key_id=answer_key_id,
            item_number=item_number,
            correct_answer=str(value),
            weight=1.00,
            statement=None,
            question_id=None,
        )
        session.add(item)


def _load_legacy_omr_templates(
    session: Session,
    *,
    exam_id_is_null: bool = False,
    exam_id_is_not_null: bool = False,
):
    clauses = []
    if exam_id_is_null:
        clauses.append("exam_id IS NULL")
    if exam_id_is_not_null:
        clauses.append("exam_id IS NOT NULL")

    where_sql = " AND ".join(clauses)
    if where_sql:
        where_sql = f"WHERE {where_sql}"

    rows = session.execute(
        sa.text(
            f"""
            SELECT id, title, layout_version, total_questions, exam_id, correct_answers
            FROM omr_templates
            {where_sql}
            ORDER BY created_at
            """
        )
    ).mappings().all()

    return [
        {
            "id": _uuid_object(row["id"]),
            "title": row["title"],
            "layout_version": row["layout_version"],
            "total_questions": row["total_questions"],
            "exam_id": _uuid_object(row["exam_id"]),
            "correct_answers": _coerce_correct_answers(row["correct_answers"]),
        }
        for row in rows
        if _coerce_correct_answers(row["correct_answers"])
    ]


def _coerce_correct_answers(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return None
    return raw_value


def _load_legacy_questions(session: Session):
    bind = session.get_bind()
    table_name = _legacy_questions_table_name(bind)
    if table_name is None:
        return []

    rows = session.execute(
        sa.text(
            f"""
            SELECT id, exam_id, question_number, statement, correct_option, weight
            FROM {table_name}
            ORDER BY exam_id, question_number
            """
        )
    ).mappings().all()

    return [
        {
            "id": _uuid_object(row["id"]),
            "exam_id": _uuid_object(row["exam_id"]),
            "question_number": row["question_number"],
            "statement": row["statement"],
            "correct_option": row["correct_option"],
            "weight": row["weight"],
        }
        for row in rows
    ]


def _legacy_questions_table_name(bind) -> str | None:
    inspector = inspect(bind)
    legacy_required = {"exam_id", "question_number", "correct_option", "weight"}

    table_name = "questions_legacy"
    if table_name not in inspector.get_table_names():
        return None

    column_names = {column["name"] for column in inspector.get_columns(table_name)}
    if legacy_required.issubset(column_names):
        return table_name
    return None


def _uuid_param(value):
    if value is None:
        return None
    if hasattr(value, "hex"):
        return value.hex
    return str(value).replace("-", "")


def _uuid_object(value):
    if value is None or isinstance(value, UUID):
        return value
    return UUID(str(value))


def backfill_attempt_references(bind) -> dict:
    """Backfill Attempt foreign keys and denormalized metadata from legacy rows.

    The function mirrors the Step 2 Alembic migration logic and is written
    against a generic SQLAlchemy bind so it can run in tests against SQLite
    and in the production migration against PostgreSQL.
    """
    stats = {
        "attempts_with_answer_key_backfilled": 0,
        "attempt_number_backfilled": 0,
        "source_backfilled": 0,
        "attempt_answers_with_item_backfilled": 0,
        "answered_at_backfilled": 0,
    }

    unresolved_attempts = int(
        bind.execute(
            sa.text(
                """
                SELECT COUNT(*)
                FROM attempts a
                LEFT JOIN answer_keys ak ON ak.exam_id = a.exam_id
                WHERE ak.id IS NULL
                """
            )
        ).scalar()
        or 0
    )
    if unresolved_attempts:
        raise RuntimeError(
            "Cannot backfill attempts.answer_key_id: "
            f"{unresolved_attempts} attempt(s) have no matching AnswerKey."
        )

    unresolved_answers = int(
        bind.execute(
            sa.text(
                """
                SELECT COUNT(*)
                FROM attempt_answers aa
                JOIN attempts a ON a.id = aa.attempt_id
                LEFT JOIN answer_keys ak ON ak.exam_id = a.exam_id
                LEFT JOIN answer_key_items aki
                    ON aki.answer_key_id = ak.id
                   AND aki.item_number = aa.question_number
                WHERE aki.id IS NULL
                """
            )
        ).scalar()
        or 0
    )
    if unresolved_answers:
        raise RuntimeError(
            "Cannot backfill attempt_answers.answer_key_item_id: "
            f"{unresolved_answers} row(s) have no matching AnswerKeyItem."
        )

    result = bind.execute(
        sa.text(
            """
            UPDATE attempts
            SET answer_key_id = (
                SELECT ak.id
                FROM answer_keys ak
                WHERE ak.exam_id = attempts.exam_id
            )
            WHERE answer_key_id IS NULL
            """
        )
    )
    stats["attempts_with_answer_key_backfilled"] = result.rowcount or 0

    result = bind.execute(
        sa.text(
            """
            UPDATE attempts
            SET attempt_number = 1
            WHERE attempt_number IS NULL
            """
        )
    )
    stats["attempt_number_backfilled"] = result.rowcount or 0

    result = bind.execute(
        sa.text(
            """
            UPDATE attempts
            SET source = 'OMR'
            WHERE source IS NULL
            """
        )
    )
    stats["source_backfilled"] = result.rowcount or 0

    result = bind.execute(
        sa.text(
            """
            UPDATE attempt_answers
            SET answer_key_item_id = (
                SELECT aki.id
                FROM answer_key_items aki
                JOIN answer_keys ak ON ak.id = aki.answer_key_id
                JOIN attempts a ON a.exam_id = ak.exam_id
                WHERE a.id = attempt_answers.attempt_id
                  AND aki.item_number = attempt_answers.question_number
            )
            WHERE answer_key_item_id IS NULL
            """
        )
    )
    stats["attempt_answers_with_item_backfilled"] = result.rowcount or 0

    result = bind.execute(
        sa.text(
            """
            UPDATE attempt_answers
            SET answered_at = COALESCE(
                (
                    SELECT a.completed_at
                    FROM attempts a
                    WHERE a.id = attempt_answers.attempt_id
                ),
                created_at
            )
            WHERE answered_at IS NULL
            """
        )
    )
    stats["answered_at_backfilled"] = result.rowcount or 0

    remaining_attempts = int(
        bind.execute(
            sa.text(
                """
                SELECT COUNT(*)
                FROM attempts
                WHERE answer_key_id IS NULL
                """
            )
        ).scalar()
        or 0
    )
    if remaining_attempts:
        raise RuntimeError(
            "attempts.answer_key_id backfill left NULL values behind."
        )

    remaining_answers = int(
        bind.execute(
            sa.text(
                """
                SELECT COUNT(*)
                FROM attempt_answers
                WHERE answer_key_item_id IS NULL
                """
            )
        ).scalar()
        or 0
    )
    if remaining_answers:
        raise RuntimeError(
            "attempt_answers.answer_key_item_id backfill left NULL values behind."
        )

    return stats
