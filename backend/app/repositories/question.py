from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.question import Question
from app.models.skill import Skill
from app.schemas.exam import QuestionCreate


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        question_id: str | UUID,
        include_inactive: bool = False,
    ) -> Optional[Question]:
        if isinstance(question_id, str):
            question_id = UUID(question_id)
        query = self.db.query(Question).options(joinedload(Question.skills)).filter(
            Question.id == question_id
        )
        if not include_inactive:
            query = query.filter(Question.is_active.is_(True))
        return query.first()

    def get_all(
        self,
        *,
        query_text: str = "",
        skill_id: UUID | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Question]:
        query = self.db.query(Question).options(joinedload(Question.skills))
        if not include_inactive:
            query = query.filter(Question.is_active.is_(True))
        if query_text.strip():
            like = f"%{query_text.strip()}%"
            query = query.filter(Question.statement.ilike(like))
        if skill_id is not None:
            query = query.join(Question.skills).filter(Skill.id == skill_id)
        return query.distinct().order_by(Question.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, question_in: QuestionCreate, *, created_by: UUID) -> Question:
        skill_ids = list(question_in.skill_ids or [])
        skills = []
        if skill_ids:
            skills = self.db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
            found_ids = {skill.id for skill in skills}
            missing_ids = [skill_id for skill_id in skill_ids if skill_id not in found_ids]
            if missing_ids:
                raise ValueError(f"Skill {missing_ids[0]} not found.")

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
        self.db.add(question)
        self.db.flush()

        if skills:
            question.skills = skills

        self.db.commit()
        self.db.refresh(question)
        return question
