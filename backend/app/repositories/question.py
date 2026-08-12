from typing import Optional
from uuid import UUID

from sqlalchemy import String as SAString
from sqlalchemy import cast, or_
from sqlalchemy.orm import Session, joinedload

from app.models.question import Question
from app.models.skill import Skill
from app.schemas.exam import QuestionCreate, QuestionUpdate


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def _resolve_skills(self, skill_ids: list[UUID] | None) -> list[Skill]:
        ids = list(skill_ids or [])
        if not ids:
            return []
        skills = self.db.query(Skill).filter(Skill.id.in_(ids)).all()
        found_ids = {skill.id for skill in skills}
        missing_ids = [skill_id for skill_id in ids if skill_id not in found_ids]
        if missing_ids:
            raise ValueError(f"Skill {missing_ids[0]} not found.")
        return skills

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
            query = (
                query.outerjoin(Question.skills).filter(
                    or_(
                        Question.statement.ilike(like),
                        Question.subject.ilike(like),
                        Question.difficulty.ilike(like),
                        cast(Question.tags, SAString).ilike(like),
                        Skill.code.ilike(like),
                        Skill.description.ilike(like),
                    )
                )
            )
        if skill_id is not None:
            query = query.join(Question.skills).filter(Skill.id == skill_id)
        return query.distinct().order_by(Question.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, question_in: QuestionCreate, *, created_by: UUID) -> Question:
        skills = self._resolve_skills(question_in.skill_ids)

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

    def update(self, question: Question, question_in: QuestionUpdate, *, updated_by: UUID) -> Question:
        if not question.is_active:
            raise ValueError("Inactive questions cannot be versioned.")

        payload = question_in.model_dump(exclude_unset=True)
        skill_ids = payload.pop("skill_ids", None)
        skills = self._resolve_skills(skill_ids) if skill_ids is not None else list(question.skills)

        versioned_question = Question(
            parent_id=question.id,
            version=question.version + 1,
            is_active=True,
            statement=payload.get("statement", question.statement),
            type=payload.get("type", question.type),
            options=payload.get("options", question.options),
            correct_answer=payload.get("correct_answer", question.correct_answer),
            explanation=payload.get("explanation", question.explanation),
            image_url=payload.get("image_url", question.image_url),
            subject=payload.get("subject", question.subject),
            difficulty=payload.get("difficulty", question.difficulty),
            tags=payload.get("tags", question.tags),
            created_by=updated_by,
        )
        self.db.add(versioned_question)
        self.db.flush()
        if skills:
            versioned_question.skills = skills

        question.is_active = False
        self.db.commit()
        self.db.refresh(versioned_question)
        return versioned_question

    def deactivate(self, question: Question) -> Question:
        question.is_active = False
        self.db.commit()
        self.db.refresh(question)
        return question
