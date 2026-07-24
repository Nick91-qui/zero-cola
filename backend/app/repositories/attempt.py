from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.attempt import Attempt, AttemptAnswer


class AttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_attempt(
        self,
        exam_id: UUID,
        student_id: Optional[UUID],
        student_code: Optional[str],
        omr_scan_id: Optional[UUID],
        total_questions: int,
        correct_answers: int,
        incorrect_answers: int,
        accuracy_percentage: Decimal,
        raw_score: Decimal,
        final_score: Decimal,
        status: str = "graded",
    ) -> Attempt:
        attempt = Attempt(
            exam_id=exam_id,
            student_id=student_id,
            student_code=student_code,
            omr_scan_id=omr_scan_id,
            status=status,
            total_questions=total_questions,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            accuracy_percentage=accuracy_percentage,
            raw_score=raw_score,
            final_score=final_score,
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def create_answers_bulk(self, answers_data: List[dict]) -> List[AttemptAnswer]:
        answers = []
        for item in answers_data:
            ans = AttemptAnswer(
                attempt_id=item["attempt_id"],
                question_number=item["question_number"],
                question_id=item.get("question_id"),
                selected_option=item.get("selected_option"),
                correct_option=item.get("correct_option"),
                is_correct=item.get("is_correct", False),
            )
            self.db.add(ans)
            answers.append(ans)
        self.db.commit()
        return answers

    def get_by_id(self, attempt_id: str | UUID) -> Optional[Attempt]:
        if isinstance(attempt_id, str):
            attempt_id = UUID(attempt_id)
        return self.db.query(Attempt).filter(Attempt.id == attempt_id).first()

    def get_by_exam_id(self, exam_id: str | UUID) -> List[Attempt]:
        if isinstance(exam_id, str):
            exam_id = UUID(exam_id)
        return self.db.query(Attempt).filter(Attempt.exam_id == exam_id).all()

    def get_by_student_id(self, student_id: str | UUID) -> List[Attempt]:
        if isinstance(student_id, str):
            student_id = UUID(student_id)
        return self.db.query(Attempt).filter(Attempt.student_id == student_id).all()

    def get_by_omr_scan_id(self, omr_scan_id: str | UUID) -> Optional[Attempt]:
        if isinstance(omr_scan_id, str):
            omr_scan_id = UUID(omr_scan_id)
        return self.db.query(Attempt).filter(Attempt.omr_scan_id == omr_scan_id).first()
