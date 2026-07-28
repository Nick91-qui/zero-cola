"""Tests for the AnswerKey backfill logic (Step 1 — AnswerKey Foundation).

These tests verify the backfill algorithm using the ORM-based backfill
function (app.services.backfill.backfill_answer_keys), which mirrors the
Alembic migration's raw-SQL logic.

IMPORTANT LIMITATION (Phase 0 issue P-11):
The existing test suite uses SQLite in-memory with BaseModel.metadata.create_all,
NOT Alembic migrations. Therefore these tests verify the backfill LOGIC but
do NOT verify the actual Alembic migration SQL on PostgreSQL. The migration
and the backfill module share the same algorithm; a dedicated PostgreSQL
migration integration test is recommended but out of scope for this step.
"""
from decimal import Decimal

import pytest

from app.models.answer_key import AnswerKey, AnswerKeyItem, answer_key_item_skills
from app.models.attempt import Attempt, AttemptAnswer
from app.models.enums import UserRole
from app.models.exam import Exam
from app.models.exam_question import ExamQuestion
from app.models.omr import OMRTemplate
from app.models.question import Question
from app.models.skill import Skill
from app.models.user import User
from app.services.backfill import backfill_answer_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_teacher(session) -> User:
    teacher = User(
        email="teacher_backfill@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    session.add(teacher)
    session.commit()
    return teacher


def _create_student(session, code="12345") -> User:
    student = User(
        email=f"student_{code}@cola-zero.edu",
        password_hash="hash",
        role=UserRole.STUDENT,
        student_code=code,
    )
    session.add(student)
    session.commit()
    return student


# ---------------------------------------------------------------------------
# Tests: Table existence and model structure
# ---------------------------------------------------------------------------


class TestAnswerKeyModelStructure:
    """Verify the new tables and models are correctly defined."""

    def test_answer_key_table_exists(self, test_db_session):
        """answer_keys table is created by metadata.create_all."""
        from sqlalchemy import inspect

        inspector = inspect(test_db_session.bind)
        assert "answer_keys" in inspector.get_table_names()

    def test_answer_key_items_table_exists(self, test_db_session):
        from sqlalchemy import inspect

        inspector = inspect(test_db_session.bind)
        assert "answer_key_items" in inspector.get_table_names()

    def test_answer_key_item_skills_table_exists(self, test_db_session):
        from sqlalchemy import inspect

        inspector = inspect(test_db_session.bind)
        assert "answer_key_item_skills" in inspector.get_table_names()

    def test_exam_questions_table_exists(self, test_db_session):
        from sqlalchemy import inspect

        inspector = inspect(test_db_session.bind)
        assert "exam_questions" in inspector.get_table_names()

    def test_answer_key_has_unique_exam_id(self, test_db_session):
        """The 1:1 constraint on exam_id should be enforced."""
        teacher = _create_teacher(test_db_session)
        exam = Exam(
            title="Test Exam",
            teacher_id=teacher.id,
            total_questions=5,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        ak1 = AnswerKey(exam_id=exam.id, is_published=False)
        test_db_session.add(ak1)
        test_db_session.commit()

        ak2 = AnswerKey(exam_id=exam.id, is_published=False)
        test_db_session.add(ak2)
        with pytest.raises(Exception):
            test_db_session.commit()
        test_db_session.rollback()

    def test_answer_key_item_unique_constraint(self, test_db_session):
        """UNIQUE(answer_key_id, item_number) is enforced."""
        teacher = _create_teacher(test_db_session)
        exam = Exam(
            title="Test Exam",
            teacher_id=teacher.id,
            total_questions=5,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        ak = AnswerKey(exam_id=exam.id, is_published=False)
        test_db_session.add(ak)
        test_db_session.commit()

        item1 = AnswerKeyItem(
            answer_key_id=ak.id, item_number=1, correct_answer="A", weight=Decimal("1.00")
        )
        test_db_session.add(item1)
        test_db_session.commit()

        item2 = AnswerKeyItem(
            answer_key_id=ak.id, item_number=1, correct_answer="B", weight=Decimal("1.00")
        )
        test_db_session.add(item2)
        with pytest.raises(Exception):
            test_db_session.commit()
        test_db_session.rollback()


# ---------------------------------------------------------------------------
# Tests: Backfill — Scenario A (orphan OMR templates)
# ---------------------------------------------------------------------------


class TestBackfillOrphanTemplates:
    """Scenario A: OMRTemplate with correct_answers but no Exam (exam_id is NULL)."""

    def test_orphan_template_gets_materialized_exam(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        tmpl = OMRTemplate(
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A", "2": "B", "3": "C"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        stats = backfill_answer_keys(test_db_session)

        assert stats["orphan_templates_materialized"] == 1
        assert stats["answer_keys_created"] >= 1

        # Template should now have exam_id set
        test_db_session.refresh(tmpl)
        assert tmpl.exam_id is not None

        # The materialized exam should exist
        exam = test_db_session.query(Exam).filter(Exam.id == tmpl.exam_id).first()
        assert exam is not None
        assert exam.title is not None
        assert exam.teacher_id == teacher.id
        assert exam.omr_template_id == tmpl.id

    def test_orphan_template_answer_key_has_items(self, test_db_session):
        _create_teacher(test_db_session)

        tmpl = OMRTemplate(
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A", "2": "B", "3": "C"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        backfill_answer_keys(test_db_session)

        test_db_session.refresh(tmpl)
        ak = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == tmpl.exam_id)
            .first()
        )
        assert ak is not None
        assert len(ak.items) == 3

        # Verify item numbers and correct answers
        items_by_number = {item.item_number: item for item in ak.items}
        assert items_by_number[1].correct_answer == "A"
        assert items_by_number[2].correct_answer == "B"
        assert items_by_number[3].correct_answer == "C"

    def test_orphan_template_without_teacher_raises(self, test_db_session):
        """If no teacher/admin exists, orphan template materialization aborts."""
        tmpl = OMRTemplate(
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        with pytest.raises(RuntimeError, match="no active TEACHER or ADMIN"):
            backfill_answer_keys(test_db_session)


# ---------------------------------------------------------------------------
# Tests: Backfill — Scenario B (Exam with OMR template + correct_answers)
# ---------------------------------------------------------------------------


class TestBackfillExamWithOMR:
    """Scenario B: Exam already exists, has OMR template with correct_answers."""

    def test_exam_with_omr_template_gets_answer_key(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova com OMR",
            teacher_id=teacher.id,
            total_questions=20,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        tmpl = OMRTemplate(
            exam_id=exam.id,
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A", "2": "C", "3": "B"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        stats = backfill_answer_keys(test_db_session)

        assert stats["exams_with_omr_backfilled"] == 1

        ak = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam.id)
            .first()
        )
        assert ak is not None
        assert len(ak.items) == 3

    def test_exam_with_omr_uses_template_correct_answers(self, test_db_session):
        """Correct answers come from omr_templates.correct_answers (preferred source)."""
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova com OMR",
            teacher_id=teacher.id,
            total_questions=3,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        # OMR template says Q1=A, Q2=C, Q3=B
        tmpl = OMRTemplate(
            exam_id=exam.id,
            layout_version="v1_std_20q",
            total_questions=3,
            correct_answers={"1": "A", "2": "C", "3": "B"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        # Also create legacy questions with DIFFERENT correct_option (to test precedence)
        for q_num, correct in [(1, "B"), (2, "A"), (3, "D")]:
            q = Question(
                exam_id=exam.id,
                question_number=q_num,
                correct_option=correct,
                weight=Decimal("1.00"),
            )
            test_db_session.add(q)
        test_db_session.commit()

        backfill_answer_keys(test_db_session)

        ak = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam.id)
            .first()
        )
        assert ak is not None
        items_by_number = {item.item_number: item for item in ak.items}
        # OMR template source should win
        assert items_by_number[1].correct_answer == "A"
        assert items_by_number[2].correct_answer == "C"
        assert items_by_number[3].correct_answer == "B"


# ---------------------------------------------------------------------------
# Tests: Backfill — Scenario C (Exam with questions, no OMR correct_answers)
# ---------------------------------------------------------------------------


class TestBackfillExamWithQuestionsOnly:
    """Scenario C: Exam with legacy questions but no OMR template (or template without correct_answers)."""

    def test_exam_with_questions_no_template_gets_answer_key(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova sem OMR",
            teacher_id=teacher.id,
            total_questions=5,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        for q_num, correct in [(1, "A"), (2, "B"), (3, "C"), (4, "D"), (5, "E")]:
            q = Question(
                exam_id=exam.id,
                question_number=q_num,
                correct_option=correct,
                weight=Decimal("2.00"),
                statement=f"Questão {q_num}",
            )
            test_db_session.add(q)
        test_db_session.commit()

        stats = backfill_answer_keys(test_db_session)

        assert stats["exams_with_questions_backfilled"] == 1

        ak = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam.id)
            .first()
        )
        assert ak is not None
        assert len(ak.items) == 5

        items_by_number = {item.item_number: item for item in ak.items}
        assert items_by_number[1].correct_answer == "A"
        assert items_by_number[2].correct_answer == "B"
        assert items_by_number[1].weight == Decimal("2.00")
        assert items_by_number[1].statement == "Questão 1"

    def test_exam_with_questions_and_template_without_correct_answers(self, test_db_session):
        """If template exists but has no correct_answers, fall back to questions."""
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova com template sem gabarito",
            teacher_id=teacher.id,
            total_questions=2,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        tmpl = OMRTemplate(
            exam_id=exam.id,
            layout_version="v1_std_20q",
            total_questions=2,
            correct_answers=None,
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        q1 = Question(
            exam_id=exam.id, question_number=1, correct_option="A", weight=Decimal("1.00")
        )
        q2 = Question(
            exam_id=exam.id, question_number=2, correct_option="C", weight=Decimal("1.00")
        )
        test_db_session.add_all([q1, q2])
        test_db_session.commit()

        backfill_answer_keys(test_db_session)

        ak = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam.id)
            .first()
        )
        assert ak is not None
        assert len(ak.items) == 2
        items_by_number = {item.item_number: item for item in ak.items}
        assert items_by_number[1].correct_answer == "A"
        assert items_by_number[2].correct_answer == "C"


# ---------------------------------------------------------------------------
# Tests: Backfill — Scenario D (is_published for graded attempts)
# ---------------------------------------------------------------------------


class TestBackfillPublishedFlag:
    """Scenario D: AnswerKey.is_published should be TRUE for exams with graded attempts."""

    def test_graded_attempt_marks_key_as_published(self, test_db_session):
        teacher = _create_teacher(test_db_session)
        student = _create_student(test_db_session)

        exam = Exam(
            title="Prova com tentativa",
            teacher_id=teacher.id,
            total_questions=2,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        # Create a graded attempt
        attempt = Attempt(
            exam_id=exam.id,
            student_id=student.id,
            student_code="12345",
            status="graded",
            total_questions=2,
            correct_answers=1,
            incorrect_answers=1,
            accuracy_percentage=Decimal("50.00"),
            raw_score=Decimal("1.00"),
            final_score=Decimal("5.00"),
        )
        test_db_session.add(attempt)
        test_db_session.commit()

        # Create OMR template with correct_answers so the exam gets an answer key
        tmpl = OMRTemplate(
            exam_id=exam.id,
            layout_version="v1_std_20q",
            total_questions=2,
            correct_answers={"1": "A", "2": "B"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        backfill_answer_keys(test_db_session)

        ak = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam.id)
            .first()
        )
        assert ak is not None
        assert ak.is_published is True
        assert ak.published_at is not None


# ---------------------------------------------------------------------------
# Tests: Backfill — Idempotency and completeness
# ---------------------------------------------------------------------------


class TestBackfillIdempotency:
    """Running backfill twice should not create duplicate answer keys."""

    def test_backfill_is_idempotent(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Prova idempotente",
            teacher_id=teacher.id,
            total_questions=3,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        tmpl = OMRTemplate(
            exam_id=exam.id,
            layout_version="v1_std_20q",
            total_questions=3,
            correct_answers={"1": "A", "2": "B", "3": "C"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        # First run
        backfill_answer_keys(test_db_session)
        keys_after_first = test_db_session.query(AnswerKey).count()
        items_after_first = test_db_session.query(AnswerKeyItem).count()
        assert keys_after_first == 1
        assert items_after_first == 3

        # Second run — should not create duplicates
        backfill_answer_keys(test_db_session)
        keys_after_second = test_db_session.query(AnswerKey).count()
        items_after_second = test_db_session.query(AnswerKeyItem).count()
        assert keys_after_second == 1
        assert items_after_second == 3


class TestBackfillCompleteness:
    """Every exam that can have an answer key should get one."""

    def test_every_exam_with_data_gets_answer_key(self, test_db_session):
        teacher = _create_teacher(test_db_session)

        # Exam 1: with OMR template
        exam1 = Exam(
            title="Exam OMR",
            teacher_id=teacher.id,
            total_questions=2,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam1)
        test_db_session.commit()

        tmpl1 = OMRTemplate(
            exam_id=exam1.id,
            layout_version="v1_std_20q",
            total_questions=2,
            correct_answers={"1": "A", "2": "B"},
            is_active=True,
        )
        test_db_session.add(tmpl1)

        # Exam 2: with questions only
        exam2 = Exam(
            title="Exam Questions",
            teacher_id=teacher.id,
            total_questions=2,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam2)
        test_db_session.commit()

        for q_num in [1, 2]:
            test_db_session.add(
                Question(
                    exam_id=exam2.id,
                    question_number=q_num,
                    correct_option="C",
                    weight=Decimal("1.00"),
                )
            )

        # Orphan template (no exam)
        tmpl_orphan = OMRTemplate(
            layout_version="v1_std_20q",
            total_questions=1,
            correct_answers={"1": "D"},
            is_active=True,
        )
        test_db_session.add(tmpl_orphan)
        test_db_session.commit()

        backfill_answer_keys(test_db_session)

        # All three should have answer keys
        ak1 = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam1.id)
            .first()
        )
        ak2 = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == exam2.id)
            .first()
        )
        assert ak1 is not None
        assert ak2 is not None

        test_db_session.refresh(tmpl_orphan)
        assert tmpl_orphan.exam_id is not None
        ak_orphan = (
            test_db_session.query(AnswerKey)
            .filter(AnswerKey.exam_id == tmpl_orphan.exam_id)
            .first()
        )
        assert ak_orphan is not None

        # Total: 3 answer keys
        assert test_db_session.query(AnswerKey).count() == 3


# ---------------------------------------------------------------------------
# Tests: Existing OMR flow unchanged (regression)
# ---------------------------------------------------------------------------


class TestExistingOMRFlowUnchanged:
    """Verify that the existing OMR flow still works after the new tables are added.

    This is a regression test — the new tables exist but no code reads from them yet.
    The legacy paths (omr_templates.correct_answers, questions.correct_option) should
    still function exactly as before.
    """

    def test_omr_template_creation_still_works(self, test_db_session):
        """OMRTemplate with correct_answers can still be created (legacy field preserved)."""
        tmpl = OMRTemplate(
            layout_version="v1_std_20q",
            total_questions=20,
            correct_answers={"1": "A", "2": "B"},
            is_active=True,
        )
        test_db_session.add(tmpl)
        test_db_session.commit()

        test_db_session.refresh(tmpl)
        assert tmpl.id is not None
        assert tmpl.correct_answers == {"1": "A", "2": "B"}

    def test_exam_creation_with_questions_still_works(self, test_db_session):
        """Legacy exam-bound Question creation still works."""
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Legacy Exam",
            teacher_id=teacher.id,
            total_questions=3,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        q = Question(
            exam_id=exam.id,
            question_number=1,
            correct_option="A",
            weight=Decimal("1.00"),
        )
        test_db_session.add(q)
        test_db_session.commit()

        assert q.id is not None
        assert q.exam_id == exam.id
        assert q.correct_option == "A"

    def test_answer_key_item_skills_relationship_works(self, test_db_session):
        """The answer_key_item_skills association table supports direct skill attachment."""
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="Skill Test",
            teacher_id=teacher.id,
            total_questions=1,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        ak = AnswerKey(exam_id=exam.id, is_published=False)
        test_db_session.add(ak)
        test_db_session.commit()

        item = AnswerKeyItem(
            answer_key_id=ak.id, item_number=1, correct_answer="A", weight=Decimal("1.00")
        )
        test_db_session.add(item)
        test_db_session.commit()

        skill = Skill(
            code="EF01M01",
            description="Contar até 10",
            subject="Matemática",
            curriculum="BNCC",
        )
        test_db_session.add(skill)
        test_db_session.commit()

        item.skills.append(skill)
        test_db_session.commit()

        test_db_session.refresh(item)
        assert len(item.skills) == 1
        assert item.skills[0].code == "EF01M01"

    def test_exam_question_table_works(self, test_db_session):
        """ExamQuestion association table is functional (empty, for future Workflow A)."""
        teacher = _create_teacher(test_db_session)

        exam = Exam(
            title="EQ Test",
            teacher_id=teacher.id,
            total_questions=1,
            max_score=Decimal("10.00"),
            is_active=True,
        )
        test_db_session.add(exam)
        test_db_session.commit()

        q = Question(
            exam_id=exam.id,
            question_number=1,
            correct_option="A",
            weight=Decimal("1.00"),
        )
        test_db_session.add(q)
        test_db_session.commit()

        eq = ExamQuestion(
            exam_id=exam.id,
            question_id=q.id,
            display_order=1,
            weight=Decimal("100.00"),
        )
        test_db_session.add(eq)
        test_db_session.commit()

        assert eq.id is not None
        assert eq.exam_id == exam.id
        assert eq.question_id == q.id
        assert eq.display_order == 1
