from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.skill import SkillCreate


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, skill_in: SkillCreate) -> Skill:
        db_skill = Skill(
            code=skill_in.code,
            description=skill_in.description,
            subject=skill_in.subject,
            grade_level=skill_in.grade_level,
            curriculum=skill_in.curriculum or "BNCC",
        )
        self.db.add(db_skill)
        self.db.commit()
        self.db.refresh(db_skill)
        return db_skill

    def get_by_id(self, skill_id: str | UUID) -> Optional[Skill]:
        if isinstance(skill_id, str):
            skill_id = UUID(skill_id)
        return self.db.query(Skill).filter(Skill.id == skill_id).first()

    def get_by_code(self, code: str) -> Optional[Skill]:
        return self.db.query(Skill).filter(Skill.code == code).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Skill]:
        return self.db.query(Skill).order_by(Skill.code.asc()).offset(skip).limit(limit).all()
