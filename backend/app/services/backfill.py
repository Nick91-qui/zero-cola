"""Backfill logic for AnswerKey foundation (Steps 1-2).

This module contains the same backfill logic as the Alembic migration
`a1b2c3d4e5f6_introduce_answer_keys.py`, extracted as a testable Python
function. The Alembic migration calls the same algorithm via raw SQL;
this module uses SQLAlchemy ORM for testability with the SQLite-based
test suite.

The production migration uses raw SQL for performance and to avoid ORM
session issues inside Alembic. This module exists solely for testing.
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.enums import UserRole
from app.models.exam import Exam
from app.models.omr import OMRTemplate
from app.models.question import Question
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
    all_orphan_candidates = (
        session.query(OMRTemplate)
        .filter(OMRTemplate.exam_id.is_(None))
        .all()
    )
    # Filter in Python: correct_answers must be a non-empty dict
    # (JSON NULL handling differs between SQLite and PostgreSQL)
    orphan_templates = [t for t in all_orphan_candidates if t.correct_answers]

    if orphan_templates and default_teacher is None:
        raise RuntimeError(
            f"Cannot materialize {len(orphan_templates)} orphan OMR template(s): "
            "no active TEACHER or ADMIN user found."
        )

    for tmpl in orphan_templates:
        tmpl_title = tmpl.title or f"Avaliação OMR {tmpl.layout_version}"

        new_exam = Exam(
            title=tmpl_title,
            teacher_id=default_teacher.id,
            omr_template_id=tmpl.id,
            total_questions=tmpl.total_questions,
            max_score=10.00,
            is_active=True,
        )
        session.add(new_exam)
        session.flush()

        # Link template to exam
        tmpl.exam_id = new_exam.id
        session.flush()

        ak = AnswerKey(
            exam_id=new_exam.id,
            is_published=False,
        )
        session.add(ak)
        session.flush()

        _create_items_from_dict(session, ak.id, tmpl.correct_answers)
        stats["orphan_templates_materialized"] += 1
        stats["answer_keys_created"] += 1

    # --- Scenario B: Exams with OMR template that has correct_answers ---
    existing_answer_key_exam_ids = session.query(AnswerKey.exam_id).all()
    existing_ak_set = {row[0] for row in existing_answer_key_exam_ids}

    # Fetch templates with exam_id set, filter correct_answers in Python
    all_linked_templates = (
        session.query(OMRTemplate)
        .filter(OMRTemplate.exam_id.isnot(None))
        .all()
    )
    templates_with_answers = [t for t in all_linked_templates if t.correct_answers]

    for tmpl in templates_with_answers:
        if tmpl.exam_id in existing_ak_set:
            continue

        ak = AnswerKey(exam_id=tmpl.exam_id, is_published=False)
        session.add(ak)
        session.flush()

        _create_items_from_dict(session, ak.id, tmpl.correct_answers)
        stats["exams_with_omr_backfilled"] += 1
        stats["answer_keys_created"] += 1
        existing_ak_set.add(tmpl.exam_id)

    # --- Scenario C: Exams with legacy questions but no AnswerKey ---
    question_exam_ids = select(Question.exam_id).distinct()
    exams_with_questions = (
        session.query(Exam)
        .filter(Exam.id.in_(question_exam_ids))
        .all()
    )

    for exam in exams_with_questions:
        if exam.id in existing_ak_set:
            continue

        # Get correct_answers from template if available
        template_correct = None
        if exam.omr_template_id is not None:
            tmpl = session.get(OMRTemplate, exam.omr_template_id)
            if tmpl and tmpl.correct_answers:
                template_correct = tmpl.correct_answers

        # Get legacy questions
        questions = (
            session.query(Question)
            .filter(Question.exam_id == exam.id)
            .order_by(Question.question_number)
            .all()
        )

        if not questions:
            continue

        ak = AnswerKey(exam_id=exam.id, is_published=False)
        session.add(ak)
        session.flush()

        for q in questions:
            # COALESCE: prefer OMR template, fall back to question
            correct_answer = None
            if template_correct:
                correct_answer = template_correct.get(str(q.question_number))
                if correct_answer is None:
                    correct_answer = template_correct.get(f"q{q.question_number}")

            if correct_answer is None:
                correct_answer = q.correct_option

            if correct_answer is None:
                continue

            item = AnswerKeyItem(
                answer_key_id=ak.id,
                item_number=q.question_number,
                correct_answer=str(correct_answer),
                weight=q.weight or 1.00,
                statement=q.statement,
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
            SET answered_at = created_at
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
