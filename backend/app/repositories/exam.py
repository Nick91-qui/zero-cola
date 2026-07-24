from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question
from app.schemas.exam import ExamCreate, ExamUpdate


class ExamRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, exam_in: ExamCreate, teacher_id: UUID) -> Exam:
        db_exam = Exam(
            title=exam_in.title,
            description=exam_in.description,
            teacher_id=teacher_id,
            class_id=exam_in.class_id,
            omr_template_id=exam_in.omr_template_id,
            total_questions=exam_in.total_questions,
            max_score=exam_in.max_score,
            is_active=True,
        )
        self.db.add(db_exam)
        self.db.commit()
        self.db.refresh(db_exam)
        return db_exam

    def get_by_id(self, exam_id: str | UUID, include_inactive: bool = False) -> Optional[Exam]:
        if isinstance(exam_id, str):
            exam_id = UUID(exam_id)
        query = self.db.query(Exam).filter(Exam.id == exam_id)
        if not include_inactive:
            query = query.filter(Exam.is_active.is_(True))
        return query.first()

    def get_all(
        self,
        teacher_id: Optional[UUID] = None,
        class_id: Optional[str] = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Exam]:
        query = self.db.query(Exam)
        if not include_inactive:
            query = query.filter(Exam.is_active.is_(True))
        if teacher_id:
            query = query.filter(Exam.teacher_id == teacher_id)
        if class_id:
            query = query.filter(Exam.class_id == class_id)
        return query.order_by(Exam.created_at.desc()).offset(skip).limit(limit).all()

    def update(self, exam_id: str | UUID, update_data: ExamUpdate | dict) -> Optional[Exam]:
        exam = self.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return None
        data = update_data if isinstance(update_data, dict) else update_data.model_dump(exclude_unset=True)
        for key, value in data.items():
            if hasattr(exam, key) and value is not None:
                setattr(exam, key, value)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def soft_delete(self, exam_id: str | UUID) -> bool:
        exam = self.get_by_id(exam_id, include_inactive=True)
        if not exam:
            return False
        exam.is_active = False
        exam.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def create_questions_bulk(
        self,
        exam_id: UUID,
        correct_answers: dict[str, str],
        weight: Decimal = Decimal("1.00"),
    ) -> List[Question]:
        questions = []
        for q_num_str, correct_opt in correct_answers.items():
            q_num = int(q_num_str.replace("q", "").replace("Q", ""))
            q = Question(
                exam_id=exam_id,
                question_number=q_num,
                correct_option=correct_opt,
                weight=weight,
            )
            self.db.add(q)
            questions.append(q)
        self.db.commit()
        return questions
