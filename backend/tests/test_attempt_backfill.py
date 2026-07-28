from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.models.attempt import Attempt, AttemptAnswer
from app.models.enums import UserRole
from app.models.exam import Exam
from app.models.user import User
from app.services.backfill import backfill_attempt_references

LEGACY_CREATED_AT = datetime(2026, 7, 28, 9, 0, tzinfo=timezone.utc)
LEGACY_COMPLETED_AT = datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc)


def _create_teacher(session) -> User:
    teacher = User(
        email="teacher_attempt_backfill@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    session.add(teacher)
    session.commit()
    return teacher


def _create_legacy_attempt_schema(connection, *, enforce_source_check: bool = False) -> None:
    source_check = ""
    if enforce_source_check:
        source_check = ", CHECK (source IN ('OMR', 'ONLINE'))"

    connection.exec_driver_sql(
        """
        CREATE TABLE exams (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            teacher_id TEXT NOT NULL,
            total_questions INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.exec_driver_sql(
        """
        CREATE TABLE answer_keys (
            id TEXT PRIMARY KEY,
            exam_id TEXT NOT NULL UNIQUE
        )
        """
    )
    connection.exec_driver_sql(
        """
        CREATE TABLE answer_key_items (
            id TEXT PRIMARY KEY,
            answer_key_id TEXT NOT NULL,
            item_number INTEGER NOT NULL,
            correct_answer TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    connection.exec_driver_sql(
        f"""
        CREATE TABLE attempts (
            id TEXT PRIMARY KEY,
            exam_id TEXT NOT NULL,
            student_id TEXT,
            student_code TEXT,
            omr_scan_id TEXT,
            answer_key_id TEXT,
            attempt_number INTEGER,
            status TEXT NOT NULL DEFAULT 'graded',
            source TEXT,
            total_questions INTEGER NOT NULL DEFAULT 0,
            correct_answers INTEGER NOT NULL DEFAULT 0,
            incorrect_answers INTEGER NOT NULL DEFAULT 0,
            accuracy_percentage NUMERIC NOT NULL DEFAULT 0.00,
            raw_score NUMERIC NOT NULL DEFAULT 0.00,
            final_score NUMERIC NOT NULL DEFAULT 0.00,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL{source_check}
        )
        """
    )
    connection.exec_driver_sql(
        """
        CREATE TABLE attempt_answers (
            id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL,
            question_number INTEGER NOT NULL,
            answer_key_item_id TEXT,
            question_id TEXT,
            selected_option TEXT,
            correct_option TEXT,
            is_correct INTEGER NOT NULL DEFAULT 0,
            answered_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def _seed_answer_key(
    connection,
    *,
    exam_id: str,
    answer_key_id: str,
    items: list[tuple[int, str]],
) -> None:
    connection.execute(
        text(
            "INSERT INTO exams (id, title, teacher_id, total_questions) "
            "VALUES (:id, :title, :teacher_id, :total_questions)"
        ),
        {
            "id": exam_id,
            "title": "Prova de referência",
            "teacher_id": "teacher-1",
            "total_questions": len(items),
        },
    )
    connection.execute(
        text("INSERT INTO answer_keys (id, exam_id) VALUES (:id, :exam_id)"),
        {"id": answer_key_id, "exam_id": exam_id},
    )
    for item_number, correct_answer in items:
        connection.execute(
            text(
                """
                INSERT INTO answer_key_items (
                    id,
                    answer_key_id,
                    item_number,
                    correct_answer,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :answer_key_id,
                    :item_number,
                    :correct_answer,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "id": f"{answer_key_id}-{item_number}",
                "answer_key_id": answer_key_id,
                "item_number": item_number,
                "correct_answer": correct_answer,
                "created_at": LEGACY_CREATED_AT.isoformat(),
                "updated_at": LEGACY_CREATED_AT.isoformat(),
            },
        )


def _seed_attempt(
    connection,
    *,
    attempt_id: str,
    exam_id: str,
    student_id: str | None,
    student_code: str | None,
    answers: list[tuple[int, str | None, str | None, int, str | None]],
    completed_at: datetime | None = LEGACY_COMPLETED_AT,
    created_at: datetime = LEGACY_CREATED_AT,
    attempt_number: int | None = None,
    answer_key_id: str | None = None,
    source: str | None = None,
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO attempts (
                id,
                exam_id,
                student_id,
                student_code,
                omr_scan_id,
                answer_key_id,
                attempt_number,
                status,
                source,
                total_questions,
                correct_answers,
                incorrect_answers,
                accuracy_percentage,
                raw_score,
                final_score,
                started_at,
                completed_at,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :exam_id,
                :student_id,
                :student_code,
                NULL,
                :answer_key_id,
                :attempt_number,
                'graded',
                :source,
                :total_questions,
                :correct_answers,
                :incorrect_answers,
                50,
                1,
                5,
                NULL,
                :completed_at,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": attempt_id,
            "exam_id": exam_id,
            "student_id": student_id,
            "student_code": student_code,
            "answer_key_id": answer_key_id,
            "attempt_number": attempt_number,
            "source": source,
            "total_questions": len(answers),
            "correct_answers": sum(1 for _, _, _, is_correct, _ in answers if is_correct),
            "incorrect_answers": sum(1 for _, _, _, is_correct, _ in answers if not is_correct),
            "completed_at": completed_at.isoformat() if completed_at else None,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        },
    )

    for item_index, (question_number, selected, correct, is_correct, question_id) in enumerate(
        answers,
        start=1,
    ):
        connection.execute(
            text(
                """
                INSERT INTO attempt_answers (
                    id,
                    attempt_id,
                    question_number,
                    answer_key_item_id,
                    question_id,
                    selected_option,
                    correct_option,
                    is_correct,
                    answered_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :attempt_id,
                    :question_number,
                    NULL,
                    :question_id,
                    :selected_option,
                    :correct_option,
                    :is_correct,
                    NULL,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "id": f"{attempt_id}-answer-{item_index}",
                "attempt_id": attempt_id,
                "question_number": question_number,
                "question_id": question_id,
                "selected_option": selected,
                "correct_option": correct,
                "is_correct": is_correct,
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
            },
        )


def _fetch_attempt_rows(connection, attempt_id: str):
    return connection.execute(
        text(
            """
            SELECT id, exam_id, answer_key_id, attempt_number, status, source,
                   completed_at
            FROM attempts
            WHERE id = :attempt_id
            """
        ),
        {"attempt_id": attempt_id},
    ).mappings().one()


def _fetch_answer_rows(connection, attempt_id: str):
    return connection.execute(
        text(
            """
            SELECT question_number, answer_key_item_id, question_id, answered_at
            FROM attempt_answers
            WHERE attempt_id = :attempt_id
            ORDER BY question_number
            """
        ),
        {"attempt_id": attempt_id},
    ).mappings().all()


class TestAttemptModelStructure:
    def test_attempt_model_defaults_are_not_started(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova para defaults",
            teacher_id=teacher.id,
            total_questions=1,
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        attempt = Attempt(exam_id=exam.id)
        test_db_session.add(attempt)
        test_db_session.commit()
        test_db_session.refresh(attempt)

        assert attempt.status == "not_started"
        assert attempt.attempt_number == 1
        assert attempt.source == "OMR"

    def test_attempt_answer_model_has_new_columns(self):
        assert "answer_key_item_id" in AttemptAnswer.__table__.c
        assert "answered_at" in AttemptAnswer.__table__.c
        assert AttemptAnswer.__table__.c.answer_key_item_id.nullable is True
        assert AttemptAnswer.__table__.c.answered_at.nullable is True

    def test_attempt_source_constraint_rejects_invalid_values(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova para constraint",
            teacher_id=teacher.id,
            total_questions=1,
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        attempt = Attempt(exam_id=exam.id, source="INVALID")
        test_db_session.add(attempt)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_step2_migration_source_declares_constraints(self):
        migration_path = (
            Path(__file__).resolve().parents[1]
            / "alembic"
            / "versions"
            / "b2c3d4e5f6a7_refactor_attempts_to_answer_key.py"
        )
        source = migration_path.read_text()

        assert "fk_attempts_answer_key_id_answer_keys" in source
        assert "fk_attempt_answers_answer_key_item_id_answer_key_items" in source
        assert "ck_attempts_source_valid" in source
        assert 'server_default="not_started"' in source


class TestAttemptBackfill:
    def test_backfill_uses_completed_at_when_available(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            _seed_answer_key(
                connection,
                exam_id="00000000-0000-0000-0000-000000000001",
                answer_key_id="00000000-0000-0000-0000-000000000002",
                items=[(1, "A"), (2, "C")],
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000003",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id=None,
                student_code="12345",
                answers=[
                    (1, "A", "A", 1, None),
                    (2, "B", "C", 0, None),
                ],
                completed_at=LEGACY_COMPLETED_AT,
            )

            backfill_attempt_references(connection)

            answer_rows = _fetch_answer_rows(
                connection,
                "00000000-0000-0000-0000-000000000003",
            )
            assert [row["answer_key_item_id"] for row in answer_rows] == [
                "00000000-0000-0000-0000-000000000002-1",
                "00000000-0000-0000-0000-000000000002-2",
            ]
            assert [row["question_id"] for row in answer_rows] == [None, None]
            assert [row["answered_at"] for row in answer_rows] == [
                LEGACY_COMPLETED_AT.isoformat(),
                LEGACY_COMPLETED_AT.isoformat(),
            ]
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()

    def test_backfill_is_idempotent(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            _seed_answer_key(
                connection,
                exam_id="00000000-0000-0000-0000-000000000001",
                answer_key_id="00000000-0000-0000-0000-000000000002",
                items=[(1, "A"), (2, "C")],
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000003",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id=None,
                student_code="12345",
                answers=[
                    (1, "A", "A", 1, None),
                    (2, "B", "C", 0, None),
                ],
                completed_at=LEGACY_COMPLETED_AT,
            )

            backfill_attempt_references(connection)
            first_attempt = _fetch_attempt_rows(
                connection,
                "00000000-0000-0000-0000-000000000003",
            )
            first_answers = _fetch_answer_rows(
                connection,
                "00000000-0000-0000-0000-000000000003",
            )
            first_attempt_count = connection.execute(
                text("SELECT COUNT(*) FROM attempts")
            ).scalar_one()
            first_answer_count = connection.execute(
                text("SELECT COUNT(*) FROM attempt_answers")
            ).scalar_one()

            backfill_attempt_references(connection)

            assert _fetch_attempt_rows(
                connection,
                "00000000-0000-0000-0000-000000000003",
            ) == first_attempt
            assert _fetch_answer_rows(
                connection,
                "00000000-0000-0000-0000-000000000003",
            ) == first_answers
            assert (
                connection.execute(text("SELECT COUNT(*) FROM attempts")).scalar_one()
                == first_attempt_count
            )
            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM attempt_answers")
                ).scalar_one()
                == first_answer_count
            )
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()

    def test_backfill_aborts_when_answer_key_missing(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            connection.execute(
                text(
                    """
                    INSERT INTO exams (id, title, teacher_id, total_questions)
                    VALUES ('00000000-0000-0000-0000-000000000001', 'Sem gabarito', 'teacher-1', 2)
                    """
                )
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000003",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id=None,
                student_code="12345",
                answers=[(1, "A", "A", 1, None)],
                completed_at=LEGACY_COMPLETED_AT,
            )

            with pytest.raises(RuntimeError, match="no matching AnswerKey"):
                backfill_attempt_references(connection)
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()

    def test_backfill_preserves_multiple_attempts_for_same_exam_and_student(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            _seed_answer_key(
                connection,
                exam_id="00000000-0000-0000-0000-000000000001",
                answer_key_id="00000000-0000-0000-0000-000000000002",
                items=[(1, "A"), (2, "C")],
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000003",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id="student-1",
                student_code="12345",
                answers=[
                    (1, "A", "A", 1, None),
                    (2, "B", "C", 0, None),
                ],
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000004",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id="student-1",
                student_code="12345",
                answers=[
                    (1, "A", "A", 1, None),
                    (2, "C", "C", 1, None),
                ],
            )

            backfill_attempt_references(connection)

            attempts = connection.execute(
                text(
                    """
                    SELECT id, answer_key_id, attempt_number
                    FROM attempts
                    ORDER BY id
                    """
                )
            ).mappings().all()
            assert [row["id"] for row in attempts] == [
                "00000000-0000-0000-0000-000000000003",
                "00000000-0000-0000-0000-000000000004",
            ]
            assert all(
                row["answer_key_id"] == "00000000-0000-0000-0000-000000000002"
                for row in attempts
            )
            assert [row["attempt_number"] for row in attempts] == [1, 1]

            answers = connection.execute(
                text(
                    """
                    SELECT attempt_id, question_number, answer_key_item_id
                    FROM attempt_answers
                    ORDER BY attempt_id, question_number
                    """
                )
            ).mappings().all()
            assert [row["answer_key_item_id"] for row in answers] == [
                "00000000-0000-0000-0000-000000000002-1",
                "00000000-0000-0000-0000-000000000002-2",
                "00000000-0000-0000-0000-000000000002-1",
                "00000000-0000-0000-0000-000000000002-2",
            ]
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()

    def test_backfill_aborts_when_answer_key_item_missing(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            _seed_answer_key(
                connection,
                exam_id="00000000-0000-0000-0000-000000000001",
                answer_key_id="00000000-0000-0000-0000-000000000002",
                items=[(1, "A")],
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000003",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id=None,
                student_code="12345",
                answers=[
                    (99, "B", "C", 0, None),
                ],
            )

            with pytest.raises(RuntimeError, match="no matching AnswerKeyItem"):
                backfill_attempt_references(connection)
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()

    def test_null_question_id_is_mapped_by_question_number(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            _seed_answer_key(
                connection,
                exam_id="00000000-0000-0000-0000-000000000001",
                answer_key_id="00000000-0000-0000-0000-000000000002",
                items=[(1, "A"), (2, "C")],
            )
            _seed_attempt(
                connection,
                attempt_id="00000000-0000-0000-0000-000000000003",
                exam_id="00000000-0000-0000-0000-000000000001",
                student_id=None,
                student_code="12345",
                answers=[
                    (2, "C", "C", 1, None),
                ],
            )

            backfill_attempt_references(connection)

            answer_row = _fetch_answer_rows(
                connection,
                "00000000-0000-0000-0000-000000000003",
            )[0]
            assert answer_row["question_id"] is None
            assert answer_row["answer_key_item_id"] == "00000000-0000-0000-0000-000000000002-2"
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()
