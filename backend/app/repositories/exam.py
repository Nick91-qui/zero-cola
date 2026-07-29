from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.exam_question import ExamQuestion
from app.models.question import Question
from app.models.skill import Skill
from app.schemas.exam import ExamCreate, ExamQuestionCreate, ExamUpdate, QuestionCreate


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
        data = (
            update_data
            if isinstance(update_data, dict)
            else update_data.model_dump(exclude_unset=True)
        )
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

    def create_exam_questions_bulk(
        self,
        exam_id: UUID,
        questions_in: List[ExamQuestionCreate],
        created_by: UUID,
    ) -> List[ExamQuestion]:
        exam_questions: List[ExamQuestion] = []
        for item in sorted(questions_in, key=lambda q: q.display_order):
            question = self._resolve_question(item, created_by)
            exam_question = ExamQuestion(
                exam_id=exam_id,
                question_id=question.id,
                display_order=item.display_order,
                weight=item.weight,
            )
            self.db.add(exam_question)
            exam_questions.append(exam_question)
        self.db.commit()
        return exam_questions

    def _resolve_question(
        self,
        item: ExamQuestionCreate,
        created_by: UUID,
    ) -> Question:
        if item.question_id is not None:
            question = self.db.query(Question).filter(Question.id == item.question_id).first()
            if question is None:
                raise ValueError(f"Question {item.question_id} not found.")
            return question

        if item.question is None:
            raise ValueError("ExamQuestionCreate requires either question_id or question.")

        question_in: QuestionCreate = item.question
        question = Question(
            statement=question_in.statement,
            type=question_in.type,
            options=question_in.options,
            correct_answer=question_in.correct_answer,
            explanation=question_in.explanation,
            image_url=question_in.image_url,
            subject=question_in.subject,
            difficulty=question_in.difficulty,
            tags=question_in.tags,
            created_by=created_by,
        )
        if question_in.skill_ids:
            question.skills = (
                self.db.query(Skill).filter(Skill.id.in_(question_in.skill_ids)).all()
            )
        self.db.add(question)
        self.db.flush()
        return question
