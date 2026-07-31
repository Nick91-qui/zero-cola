from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from random import Random
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.answer_key import AnswerKeyItem
from app.models.attempt import Attempt, AttemptAnswer
from app.models.enums import AttemptStatus, ExamStatus, GradeSourceType
from app.models.exam import Exam
from app.models.user import User
from app.repositories.attempt import AttemptRepository
from app.repositories.exam import ExamRepository
from app.repositories.grade import GradeRepository
from app.schemas.attempt import (
    OnlineAttemptActiveAnswerResponse,
    OnlineAttemptProgressResponse,
    OnlineAttemptQuestionResponse,
    OnlineAttemptResultResponse,
    OnlineAttemptSessionResponse,
    StudentAttemptAnswerResponse,
    StudentAttemptResponse,
)
from app.services.answer_key import AnswerKeyService
from app.services.exam import ExamService


class AttemptService:
    def __init__(self, db: Session):
        self.db = db
        self.attempt_repo = AttemptRepository(db)
        self.exam_repo = ExamRepository(db)
        self.grade_repo = GradeRepository(db)
        self.answer_key_service = AnswerKeyService(db)
        self.exam_service = ExamService(db)

    def start_online_attempt(self, exam_id: UUID, student: User) -> OnlineAttemptSessionResponse:
        exam = self._require_published_exam(exam_id, student)

        active_attempt = self.attempt_repo.get_latest_for_student_exam_source(
            exam.id,
            student.id,
            GradeSourceType.ONLINE.value,
        )
        if active_attempt and active_attempt.status in {
            AttemptStatus.NOT_STARTED.value,
            AttemptStatus.IN_PROGRESS.value,
            AttemptStatus.SUBMITTED.value,
        }:
            return self._build_session_response(active_attempt)

        graded_attempts = self.attempt_repo.count_for_student_exam_source(
            exam.id,
            student.id,
            GradeSourceType.ONLINE.value,
            statuses=[AttemptStatus.GRADED.value],
        )
        if graded_attempts >= exam.max_attempts:
            raise ValueError("Student has reached the maximum number of attempts for this exam.")

        answer_key = self.answer_key_service.require_for_exam(exam.id)
        if not answer_key.is_published:
            raise ValueError(f"Exam {exam.id} does not have a published AnswerKey.")

        items = list(answer_key.items)
        if not items:
            raise ValueError(f"Exam {exam.id} has no AnswerKeyItems.")

        now = datetime.now(timezone.utc)
        attempt = self.attempt_repo.create_attempt(
            exam_id=exam.id,
            answer_key_id=answer_key.id,
            student_id=student.id,
            student_code=student.student_code,
            omr_scan_id=None,
            total_questions=len(items),
            correct_answers=0,
            incorrect_answers=len(items),
            accuracy_percentage=Decimal("0.00"),
            raw_score=Decimal("0.00"),
            final_score=Decimal("0.00"),
            source=GradeSourceType.ONLINE.value,
            status=AttemptStatus.NOT_STARTED.value,
            attempt_number=graded_attempts + 1,
            started_at=None,
            completed_at=None,
            commit=False,
        )

        ordered_items = self._order_items_for_attempt(exam, attempt.id, items)
        answers_data = []
        for index, item in enumerate(ordered_items, start=1):
            answers_data.append(
                {
                    "attempt_id": attempt.id,
                    "question_number": index,
                    "answer_key_item_id": item.id,
                    "question_id": item.question_id,
                    "selected_option": None,
                    "correct_option": item.correct_answer,
                    "is_correct": False,
                    "answered_at": None,
                }
            )

        self.attempt_repo.create_answers_bulk(answers_data, commit=False)
        attempt.status = AttemptStatus.IN_PROGRESS.value
        attempt.started_at = now
        self.db.commit()
        self.db.refresh(attempt)
        return self._build_session_response(attempt)

    def get_current_question(
        self,
        attempt_id: UUID,
        student: User,
    ) -> OnlineAttemptSessionResponse:
        attempt = self._require_student_attempt(attempt_id, student.id)
        self._ensure_attempt_in_progress(attempt)
        self._ensure_not_expired(attempt)
        return self._build_session_response(attempt)

    def save_answer(
        self,
        attempt_id: UUID,
        question_number: int,
        selected_option: Optional[str],
        student: User,
    ) -> OnlineAttemptSessionResponse:
        attempt = self._require_student_attempt(attempt_id, student.id)
        self._ensure_attempt_in_progress(attempt)
        self._ensure_not_expired(attempt)

        answer = self.attempt_repo.get_answer_by_attempt_and_number(attempt.id, question_number)
        if answer is None:
            raise ValueError(
                f"Question number {question_number} does not exist for attempt {attempt.id}."
            )

        item = answer.answer_key_item
        if item is None:
            raise ValueError(
                f"AttemptAnswer {answer.id} is not linked to an AnswerKeyItem."
            )

        self._validate_selected_option(item, selected_option)

        answer.selected_option = selected_option
        answer.correct_option = item.correct_answer
        answer.is_correct = bool(
            selected_option is not None and selected_option == item.correct_answer
        )
        answer.answered_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(answer)
        self.db.refresh(attempt)
        return self._build_session_response(attempt)

    def next_question(
        self,
        attempt_id: UUID,
        question_number: int,
        student: User,
    ) -> OnlineAttemptSessionResponse:
        return self._navigate_question(attempt_id, question_number + 1, student)

    def previous_question(
        self,
        attempt_id: UUID,
        question_number: int,
        student: User,
    ) -> OnlineAttemptSessionResponse:
        return self._navigate_question(attempt_id, question_number - 1, student)

    def submit_attempt(self, attempt_id: UUID, student: User) -> OnlineAttemptResultResponse:
        attempt = self._require_student_attempt(attempt_id, student.id)
        if attempt.status == AttemptStatus.GRADED.value:
            return self.get_result(attempt_id, student)

        if attempt.status not in {
            AttemptStatus.IN_PROGRESS.value,
            AttemptStatus.SUBMITTED.value,
            AttemptStatus.NOT_STARTED.value,
        }:
            raise ValueError(f"Attempt {attempt.id} cannot be submitted in its current state.")

        now = datetime.now(timezone.utc)
        if attempt.status != AttemptStatus.SUBMITTED.value:
            attempt.status = AttemptStatus.SUBMITTED.value
            attempt.completed_at = now
            self.db.commit()
            self.db.refresh(attempt)

        grade_result = self._grade_attempt(attempt, student, now)

        attempt.status = AttemptStatus.GRADED.value
        self.db.commit()
        self.db.refresh(attempt)
        return self._build_result_response(attempt, grade_result)

    def get_result(self, attempt_id: UUID, student: User) -> OnlineAttemptResultResponse:
        attempt = self._require_student_attempt(attempt_id, student.id)
        if attempt.status != AttemptStatus.GRADED.value:
            grade = self.grade_repo.get_by_source(GradeSourceType.ONLINE, attempt.id)
            if grade is None:
                raise ValueError(f"Attempt {attempt.id} has not been graded yet.")
            return self._build_result_response(attempt, grade)

        grade = self.grade_repo.get_by_source(GradeSourceType.ONLINE, attempt.id)
        if grade is None:
            raise ValueError(f"Attempt {attempt.id} has not been graded yet.")
        return self._build_result_response(attempt, grade)

    def _navigate_question(
        self,
        attempt_id: UUID,
        question_number: int,
        student: User,
    ) -> OnlineAttemptSessionResponse:
        attempt = self._require_student_attempt(attempt_id, student.id)
        self._ensure_attempt_in_progress(attempt)
        self._ensure_not_expired(attempt)

        if question_number < 1 or question_number > attempt.total_questions:
            raise ValueError(
                f"Question number {question_number} is outside the attempt range."
            )
        return self._build_session_response(attempt, question_number=question_number)

    def _build_session_response(
        self,
        attempt: Attempt,
        question_number: Optional[int] = None,
    ) -> OnlineAttemptSessionResponse:
        attempt = self._load_attempt(attempt.id)
        answers = sorted(attempt.answers, key=lambda row: row.question_number)
        attempt_response = OnlineAttemptProgressResponse.model_validate(attempt)
        attempt_response.answers = [
            OnlineAttemptActiveAnswerResponse.model_validate(answer)
            for answer in answers
        ]
        current_answer = self._resolve_current_answer(answers, question_number)
        return OnlineAttemptSessionResponse(
            attempt=attempt_response,
            current_question=(
                self._build_question_response(current_answer) if current_answer else None
            ),
            total_questions=attempt.total_questions,
        )

    def _build_result_response(
        self,
        attempt: Attempt,
        grade,
    ) -> OnlineAttemptResultResponse:
        attempt = self._load_attempt(attempt.id)
        attempt_response = StudentAttemptResponse.model_validate(attempt)
        attempt_response.answers = [
            StudentAttemptAnswerResponse.model_validate(answer)
            for answer in sorted(attempt.answers, key=lambda row: row.question_number)
        ]
        return OnlineAttemptResultResponse(
            attempt=attempt_response,
            grade=grade,
        )

    def _build_question_response(
        self,
        answer: AttemptAnswer,
    ) -> OnlineAttemptQuestionResponse:
        item = answer.answer_key_item
        question = item.question if item else None
        statement = item.statement if item and item.statement is not None else (
            question.statement if question is not None else None
        )
        options = question.options if question is not None else None
        return OnlineAttemptQuestionResponse(
            question_number=answer.question_number,
            question_id=item.question_id if item is not None else answer.question_id,
            statement=statement,
            options=options,
            selected_option=answer.selected_option,
            answered_at=answer.answered_at,
        )

    def _resolve_current_answer(
        self,
        answers: list[AttemptAnswer],
        question_number: Optional[int] = None,
    ) -> Optional[AttemptAnswer]:
        if not answers:
            return None

        if question_number is not None:
            for answer in answers:
                if answer.question_number == question_number:
                    return answer
            return None

        unanswered = next((answer for answer in answers if answer.selected_option is None), None)
        return unanswered or answers[-1]

    def _load_attempt(self, attempt_id: UUID) -> Attempt:
        attempt = (
            self.db.query(Attempt)
            .options(
                selectinload(Attempt.answers).selectinload(AttemptAnswer.answer_key_item).selectinload(
                    AnswerKeyItem.question
                ),
                selectinload(Attempt.exam),
            )
            .filter(Attempt.id == attempt_id)
            .first()
        )
        if attempt is None:
            raise ValueError(f"Attempt {attempt_id} not found.")
        return attempt

    def _require_student_attempt(self, attempt_id: UUID, student_id: UUID) -> Attempt:
        attempt = self._load_attempt(attempt_id)
        if attempt.student_id != student_id:
            raise PermissionError(f"Attempt {attempt_id} does not belong to this student.")
        return attempt

    def _require_published_exam(self, exam_id: UUID, student: User) -> Exam:
        exam = self.exam_repo.get_by_id(exam_id, include_inactive=True)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found.")
        if exam.status != ExamStatus.PUBLISHED.value or not exam.is_active:
            raise ValueError(f"Exam {exam_id} must be published to start an online attempt.")

        available_exam = self.exam_service.get_exam_for_student(exam_id, student.id)
        if available_exam is None:
            raise ValueError(f"Exam {exam_id} must be published to start an online attempt.")
        if available_exam.answer_key is None or not available_exam.answer_key.is_published:
            raise ValueError(f"Exam {exam_id} must have a published AnswerKey.")
        return available_exam

    def _ensure_attempt_in_progress(self, attempt: Attempt) -> None:
        if attempt.status in {AttemptStatus.SUBMITTED.value, AttemptStatus.GRADED.value}:
            raise ValueError(f"Attempt {attempt.id} is already submitted or graded.")

    def _ensure_not_expired(self, attempt: Attempt) -> None:
        exam = attempt.exam
        if not exam or exam.total_time_seconds is None or attempt.started_at is None:
            return

        started_at = self._normalize_datetime(attempt.started_at)
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
        if elapsed > exam.total_time_seconds:
            raise ValueError(f"Attempt {attempt.id} has exceeded its time limit.")

    def _validate_selected_option(
        self,
        item: AnswerKeyItem,
        selected_option: Optional[str],
    ) -> None:
        if selected_option is None:
            return

        question = item.question
        if question is None or not question.options:
            return

        valid_options = set(question.options.keys())
        if selected_option not in valid_options:
            raise ValueError(
                f"Selected option {selected_option!r} is not valid for question {item.question_id}."
            )

    def _order_items_for_attempt(
        self,
        exam: Exam,
        attempt_id: UUID,
        items: list[AnswerKeyItem],
    ) -> list[AnswerKeyItem]:
        ordered = list(items)
        if exam.randomization_enabled:
            rng = Random(str(attempt_id))
            rng.shuffle(ordered)
        return ordered

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _grade_attempt(self, attempt: Attempt, student: User, now: datetime):
        answers = sorted(attempt.answers, key=lambda row: row.question_number)
        total_questions = len(answers)
        correct_answers = 0

        for answer in answers:
            item = answer.answer_key_item
            if item is None:
                continue

            if answer.selected_option is not None and answer.selected_option == item.correct_answer:
                correct_answers += 1
            answer.correct_option = item.correct_answer
            answer.is_correct = (
                answer.selected_option is not None and answer.selected_option == item.correct_answer
            )
            if answer.answered_at is None:
                answer.answered_at = now

        incorrect_answers = total_questions - correct_answers
        accuracy_percentage = (
            (Decimal(correct_answers) / Decimal(total_questions)) * Decimal("100.00")
            if total_questions > 0
            else Decimal("0.00")
        ).quantize(Decimal("0.01"))
        raw_score = Decimal(correct_answers).quantize(Decimal("0.01"))
        final_score = (
            (Decimal(correct_answers) / Decimal(total_questions)) * attempt.exam.max_score
            if total_questions > 0
            else Decimal("0.00")
        ).quantize(Decimal("0.01"))

        attempt.total_questions = total_questions
        attempt.correct_answers = correct_answers
        attempt.incorrect_answers = incorrect_answers
        attempt.accuracy_percentage = accuracy_percentage
        attempt.raw_score = raw_score
        attempt.final_score = final_score

        self.db.commit()
        self.db.refresh(attempt)

        return self.grade_repo.create_or_update(
            student_id=student.id,
            source_type=GradeSourceType.ONLINE,
            source_id=attempt.id,
            score=final_score,
            teacher_id=attempt.exam.teacher_id,
        )
