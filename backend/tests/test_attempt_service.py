from datetime import datetime, timedelta, timezone
from decimal import Decimal
from random import Random
from uuid import UUID

import pytest
from sqlalchemy import update

from app.models.answer_key import AnswerKey, AnswerKeyItem
from app.models.attempt import Attempt
from app.models.enums import AttemptStatus, ExamStatus, GradeSourceType, UserRole
from app.models.exam import Exam
from app.models.grade import Grade
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamQuestionCreate, QuestionCreate
from app.services.attempt import AttemptService
from app.services.class_service import ClassService
from app.services.exam import ExamService


def _create_teacher_and_student(test_db_session, *, student_code: str = "12345"):
    teacher = User(
        email=f"teacher_attempt_{student_code}@cola-zero.edu",
        password_hash="hash",
        role=UserRole.TEACHER,
    )
    student = User(
        email=f"student_attempt_{student_code}@cola-zero.edu",
        password_hash="hash",
        role=UserRole.STUDENT,
        student_code=student_code,
    )
    test_db_session.add_all([teacher, student])
    test_db_session.commit()
    return teacher, student


def _create_admin(test_db_session, *, suffix: str) -> User:
    admin = User(
        email=f"admin_attempt_{suffix}@cola-zero.edu",
        password_hash="hash",
        role=UserRole.ADMIN,
    )
    test_db_session.add(admin)
    test_db_session.commit()
    return admin


def _create_class_and_enroll_student(
    test_db_session,
    *,
    teacher: User,
    student: User,
    name: str,
    academic_period: str = "2026",
):
    admin = _create_admin(test_db_session, suffix=name.replace(" ", "_").lower())
    class_service = ClassService(test_db_session)
    class_obj = class_service.create_class(
        current_user=admin,
        name=name,
        academic_period=academic_period,
        teacher_id=teacher.id,
    )
    class_service.add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[student.id],
    )
    return class_obj, admin


def _create_workflow_a_exam(
    test_db_session,
    teacher: User,
    *,
    class_ids: list[UUID] | None = None,
    randomization_enabled: bool = False,
    max_attempts: int = 1,
    total_time_seconds: int | None = None,
) -> Exam:
    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Online Workflow A",
            total_questions=4,
            class_ids=class_ids,
            randomization_enabled=randomization_enabled,
            max_attempts=max_attempts,
            total_time_seconds=total_time_seconds,
            questions=[
                ExamQuestionCreate(
                    display_order=1,
                    question=QuestionCreate(
                        statement="Questão 1",
                        options={"A": "A", "B": "B"},
                        correct_answer="A",
                    ),
                ),
                ExamQuestionCreate(
                    display_order=2,
                    question=QuestionCreate(
                        statement="Questão 2",
                        options={"A": "A", "B": "B"},
                        correct_answer="B",
                    ),
                ),
                ExamQuestionCreate(
                    display_order=3,
                    question=QuestionCreate(
                        statement="Questão 3",
                        options={"A": "A", "B": "B"},
                        correct_answer="A",
                    ),
                ),
                ExamQuestionCreate(
                    display_order=4,
                    question=QuestionCreate(
                        statement="Questão 4",
                        options={"A": "A", "B": "B"},
                        correct_answer="B",
                    ),
                ),
            ],
        ),
        teacher_id=teacher.id,
    )
    return service.publish_exam(exam.id)


def _create_workflow_b_exam(
    test_db_session,
    teacher: User,
    *,
    class_ids: list[UUID] | None = None,
) -> Exam:
    service = ExamService(test_db_session)
    exam = service.create_exam(
        ExamCreate(
            title="Online Workflow B",
            total_questions=1,
            class_ids=class_ids,
            correct_answers={"1": "A"},
        ),
        teacher_id=teacher.id,
    )
    return service.publish_exam(exam.id)


def _answer_key_items_for_exam(test_db_session, exam_id):
    return (
        test_db_session.query(AnswerKeyItem)
        .join(AnswerKey)
        .filter(AnswerKey.exam_id == exam_id)
        .order_by(AnswerKeyItem.item_number)
        .all()
    )


def test_online_attempt_workflow_a_randomization_and_navigation(test_db_session):
    teacher, student = _create_teacher_and_student(test_db_session, student_code="11111")
    class_obj, _admin = _create_class_and_enroll_student(
        test_db_session,
        teacher=teacher,
        student=student,
        name="Turma tentativa A",
    )
    exam = _create_workflow_a_exam(
        test_db_session,
        teacher,
        class_ids=[class_obj.id],
        randomization_enabled=True,
        max_attempts=2,
    )

    service = AttemptService(test_db_session)
    session = service.start_online_attempt(exam.id, student)

    attempt = test_db_session.query(Attempt).filter(Attempt.id == session.attempt.id).one()
    assert attempt.status == AttemptStatus.IN_PROGRESS.value
    assert attempt.source == "ONLINE"
    assert attempt.answer_key_id == exam.answer_key.id
    assert session.current_question is not None
    assert "correct_answer" not in session.current_question.model_dump()
    attempt_payload = session.attempt.model_dump()
    assert "correct_answers" not in attempt_payload
    assert "incorrect_answers" not in attempt_payload
    assert "accuracy_percentage" not in attempt_payload
    assert "raw_score" not in attempt_payload
    assert "final_score" not in attempt_payload

    canonical_items = _answer_key_items_for_exam(test_db_session, exam.id)
    expected_order = list(canonical_items)
    Random(str(attempt.id)).shuffle(expected_order)

    attempt_answer_rows = sorted(attempt.answers, key=lambda row: row.question_number)
    assert [row.answer_key_item_id for row in attempt_answer_rows] == [
        item.id for item in expected_order
    ]
    assert session.current_question.question_number == 1
    assert session.current_question.statement == expected_order[0].statement

    first_answer = attempt_answer_rows[0]
    saved = service.save_answer(
        attempt.id,
        1,
        first_answer.answer_key_item.correct_answer,
        student,
    )
    assert saved.current_question is not None
    assert saved.current_question.question_number == 2

    resumed = service.start_online_attempt(exam.id, student)
    assert resumed.attempt.id == attempt.id
    assert resumed.current_question is not None
    assert resumed.current_question.question_number == 2

    next_session = service.next_question(attempt.id, 1, student)
    assert next_session.current_question is not None
    assert next_session.current_question.question_number == 2

    previous_session = service.previous_question(attempt.id, 2, student)
    assert previous_session.current_question is not None
    assert previous_session.current_question.question_number == 1


def test_online_attempt_submission_grades_against_answer_key_item(test_db_session):
    teacher, student = _create_teacher_and_student(test_db_session, student_code="22222")
    class_obj, _admin = _create_class_and_enroll_student(
        test_db_session,
        teacher=teacher,
        student=student,
        name="Turma tentativa B",
    )
    exam = _create_workflow_a_exam(test_db_session, teacher, class_ids=[class_obj.id])

    exam_row = test_db_session.query(Exam).filter(Exam.id == exam.id).one()
    source_question = exam_row.exam_questions[0].question
    assert source_question is not None
    source_question.correct_answer = "Z"
    test_db_session.commit()

    answer_key_items = _answer_key_items_for_exam(test_db_session, exam.id)
    assert answer_key_items

    service = AttemptService(test_db_session)
    session = service.start_online_attempt(exam.id, student)
    attempt = test_db_session.query(Attempt).filter(Attempt.id == session.attempt.id).one()

    for row in sorted(attempt.answers, key=lambda answer: answer.question_number):
        row_item = row.answer_key_item
        assert row_item is not None
        service.save_answer(attempt.id, row.question_number, row_item.correct_answer, student)

    result = service.submit_attempt(attempt.id, student)
    assert result.grade is not None
    assert result.grade.source_type == GradeSourceType.ONLINE
    assert result.grade.source_id == attempt.id
    assert result.grade.score == Decimal("10.00")
    assert result.attempt.status == AttemptStatus.GRADED.value
    assert all("correct_option" not in answer.model_dump() for answer in result.attempt.answers)
    assert "correct_answer" not in result.model_dump()

    grade = test_db_session.query(Grade).filter(Grade.source_id == attempt.id).one()
    assert grade.source_type == GradeSourceType.ONLINE


def test_online_attempt_respects_max_attempts_and_student_isolation(test_db_session):
    teacher, student = _create_teacher_and_student(test_db_session, student_code="33333")
    other_student = User(
        email="other_student_attempt_44444@cola-zero.edu",
        password_hash="hash",
        role=UserRole.STUDENT,
        student_code="44444",
    )
    test_db_session.add(other_student)
    test_db_session.commit()
    class_obj, admin = _create_class_and_enroll_student(
        test_db_session,
        teacher=teacher,
        student=student,
        name="Turma tentativa C",
    )
    class_service = ClassService(test_db_session)
    class_service.add_students(
        class_id=class_obj.id,
        current_user=admin,
        student_ids=[other_student.id],
    )
    exam = _create_workflow_a_exam(
        test_db_session,
        teacher,
        class_ids=[class_obj.id],
        max_attempts=1,
    )

    service = AttemptService(test_db_session)
    session = service.start_online_attempt(exam.id, student)
    service.submit_attempt(session.attempt.id, student)

    with pytest.raises(ValueError, match="maximum number of attempts"):
        service.start_online_attempt(exam.id, student)

    second_session = service.start_online_attempt(exam.id, other_student)
    assert second_session.attempt.student_id == other_student.id

    with pytest.raises(PermissionError):
        service.get_current_question(session.attempt.id, other_student)

    with pytest.raises(PermissionError):
        service.save_answer(session.attempt.id, 1, "A", other_student)


def test_online_attempt_blocks_draft_and_archived_exams(test_db_session):
    teacher, student = _create_teacher_and_student(test_db_session, student_code="55555")
    class_obj, _admin = _create_class_and_enroll_student(
        test_db_session,
        teacher=teacher,
        student=student,
        name="Turma tentativa D",
    )
    service = ExamService(test_db_session)
    draft_exam = service.create_exam(
        ExamCreate(
            title="Draft exam",
            total_questions=1,
            class_ids=[class_obj.id],
            questions=[
                ExamQuestionCreate(
                    display_order=1,
                    question=QuestionCreate(statement="Questão", correct_answer="A"),
                )
            ],
        ),
        teacher_id=teacher.id,
    )

    attempt_service = AttemptService(test_db_session)
    with pytest.raises(ValueError, match="must be published"):
        attempt_service.start_online_attempt(draft_exam.id, student)

    published_exam = service.publish_exam(draft_exam.id)
    archived_exam = service.archive_exam(published_exam.id)
    assert archived_exam.status == ExamStatus.ARCHIVED.value

    with pytest.raises(ValueError, match="must be published"):
        attempt_service.start_online_attempt(archived_exam.id, student)


def test_online_attempt_supports_workflow_b_without_question_bank(test_db_session):
    teacher, student = _create_teacher_and_student(test_db_session, student_code="66666")
    class_obj, _admin = _create_class_and_enroll_student(
        test_db_session,
        teacher=teacher,
        student=student,
        name="Turma workflow B",
    )
    exam = _create_workflow_b_exam(test_db_session, teacher, class_ids=[class_obj.id])

    service = AttemptService(test_db_session)
    session = service.start_online_attempt(exam.id, student)

    assert session.current_question is not None
    assert session.current_question.statement is None

    answer = session.attempt.answers[0]
    assert answer.question_id is None

    saved = service.save_answer(session.attempt.id, 1, "A", student)
    assert saved.current_question is not None

    result = service.submit_attempt(session.attempt.id, student)
    assert result.grade is not None
    assert result.grade.source_type == GradeSourceType.ONLINE
    assert result.attempt.answers[0].question_id is None


def test_online_attempt_time_limit_blocks_updates(test_db_session):
    teacher, student = _create_teacher_and_student(test_db_session, student_code="77777")
    class_obj, _admin = _create_class_and_enroll_student(
        test_db_session,
        teacher=teacher,
        student=student,
        name="Turma tempo",
    )
    exam = _create_workflow_a_exam(
        test_db_session,
        teacher,
        class_ids=[class_obj.id],
        total_time_seconds=60,
    )

    service = AttemptService(test_db_session)
    session = service.start_online_attempt(exam.id, student)

    test_db_session.execute(
        update(Attempt)
        .where(Attempt.id == session.attempt.id)
        .values(started_at=datetime.now(timezone.utc) - timedelta(minutes=5))
    )
    test_db_session.commit()

    with pytest.raises(ValueError, match="time limit"):
        service.save_answer(session.attempt.id, 1, "A", student)
