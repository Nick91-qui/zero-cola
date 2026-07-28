from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text

from app.models.attempt import Attempt, AttemptAnswer
from app.services.backfill import backfill_attempt_references


def _create_legacy_attempt_schema(connection) -> None:
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
        """
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
            updated_at TEXT NOT NULL
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


def _seed_attempt_backfill_data(connection) -> dict[str, str]:
    ids = {
        "exam_id": "00000000-0000-0000-0000-000000000001",
        "answer_key_id": "00000000-0000-0000-0000-000000000002",
        "attempt_id": "00000000-0000-0000-0000-000000000003",
        "item_1": "00000000-0000-0000-0000-000000000004",
        "item_2": "00000000-0000-0000-0000-000000000005",
        "aa_1": "00000000-0000-0000-0000-000000000006",
        "aa_2": "00000000-0000-0000-0000-000000000007",
    }
    timestamp = datetime(2026, 7, 28, 9, 0, tzinfo=timezone.utc).isoformat()

    connection.execute(
        text(
            "INSERT INTO exams (id, title, teacher_id, total_questions) "
            "VALUES (:id, :title, :teacher_id, :total_questions)"
        ),
        {
            "id": ids["exam_id"],
            "title": "Prova de referência",
            "teacher_id": "teacher-1",
            "total_questions": 2,
        },
    )
    connection.execute(
        text("INSERT INTO answer_keys (id, exam_id) VALUES (:id, :exam_id)"),
        {"id": ids["answer_key_id"], "exam_id": ids["exam_id"]},
    )
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
            "id": ids["item_1"],
            "answer_key_id": ids["answer_key_id"],
            "item_number": 1,
            "correct_answer": "A",
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )
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
            "id": ids["item_2"],
            "answer_key_id": ids["answer_key_id"],
            "item_number": 2,
            "correct_answer": "C",
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO attempts (
                id,
                exam_id,
                student_code,
                status,
                total_questions,
                correct_answers,
                incorrect_answers,
                accuracy_percentage,
                raw_score,
                final_score,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :exam_id,
                :student_code,
                :status,
                :total_questions,
                :correct_answers,
                :incorrect_answers,
                :accuracy_percentage,
                :raw_score,
                :final_score,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": ids["attempt_id"],
            "exam_id": ids["exam_id"],
            "student_code": "12345",
            "status": "graded",
            "total_questions": 2,
            "correct_answers": 1,
            "incorrect_answers": 1,
            "accuracy_percentage": 50,
            "raw_score": 1,
            "final_score": 5,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO attempt_answers (
                id,
                attempt_id,
                question_number,
                selected_option,
                correct_option,
                is_correct,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :attempt_id,
                :question_number,
                :selected_option,
                :correct_option,
                :is_correct,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": ids["aa_1"],
            "attempt_id": ids["attempt_id"],
            "question_number": 1,
            "selected_option": "A",
            "correct_option": "A",
            "is_correct": 1,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO attempt_answers (
                id,
                attempt_id,
                question_number,
                selected_option,
                correct_option,
                is_correct,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :attempt_id,
                :question_number,
                :selected_option,
                :correct_option,
                :is_correct,
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": ids["aa_2"],
            "attempt_id": ids["attempt_id"],
            "question_number": 2,
            "selected_option": "B",
            "correct_option": "C",
            "is_correct": 0,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )

    return ids


class TestAttemptModelStructure:
    def test_attempt_model_includes_answer_key_refs(self):
        assert "answer_key_id" in Attempt.__table__.c
        assert "attempt_number" in Attempt.__table__.c
        assert "source" in Attempt.__table__.c
        assert Attempt.__table__.c.answer_key_id.nullable is True
        assert Attempt.__table__.c.attempt_number.default.arg == 1
        assert Attempt.__table__.c.source.default.arg == "OMR"
        assert Attempt.__table__.c.status.default.arg == "not_started"

    def test_attempt_answer_model_includes_answer_key_item_ref(self):
        assert "answer_key_item_id" in AttemptAnswer.__table__.c
        assert "answered_at" in AttemptAnswer.__table__.c
        assert AttemptAnswer.__table__.c.answer_key_item_id.nullable is True
        assert AttemptAnswer.__table__.c.answered_at.nullable is True


class TestAttemptBackfill:
    def test_backfill_populates_attempt_and_answer_references(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            ids = _seed_attempt_backfill_data(connection)

            stats = backfill_attempt_references(connection)

            assert stats["attempts_with_answer_key_backfilled"] == 1
            assert stats["attempt_number_backfilled"] == 1
            assert stats["source_backfilled"] == 1
            assert stats["attempt_answers_with_item_backfilled"] == 2
            assert stats["answered_at_backfilled"] == 2

            attempt_row = connection.execute(
                text(
                    "SELECT answer_key_id, attempt_number, source "
                    "FROM attempts WHERE id = :attempt_id"
                ),
                {"attempt_id": ids["attempt_id"]},
            ).mappings().one()
            assert attempt_row["answer_key_id"] == ids["answer_key_id"]
            assert attempt_row["attempt_number"] == 1
            assert attempt_row["source"] == "OMR"

            answer_rows = connection.execute(
                text(
                    "SELECT question_number, answer_key_item_id, answered_at, created_at "
                    "FROM attempt_answers WHERE attempt_id = :attempt_id "
                    "ORDER BY question_number"
                ),
                {"attempt_id": ids["attempt_id"]},
            ).mappings().all()
            assert [row["answer_key_item_id"] for row in answer_rows] == [
                ids["item_1"],
                ids["item_2"],
            ]
            assert [row["answered_at"] for row in answer_rows] == [
                row["created_at"] for row in answer_rows
            ]
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()

    def test_backfill_aborts_when_an_answer_has_no_matching_item(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        connection = engine.connect()
        transaction = connection.begin()

        try:
            _create_legacy_attempt_schema(connection)
            ids = _seed_attempt_backfill_data(connection)
            connection.execute(
                text("UPDATE attempt_answers SET question_number = 99 WHERE id = :id"),
                {"id": ids["aa_2"]},
            )

            with pytest.raises(RuntimeError, match="no matching AnswerKeyItem"):
                backfill_attempt_references(connection)
        finally:
            transaction.rollback()
            connection.close()
            engine.dispose()
