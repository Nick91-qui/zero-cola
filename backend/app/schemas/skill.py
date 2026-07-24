from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SkillBase(BaseModel):
    code: str
    description: str
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    curriculum: Optional[str] = "BNCC"


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
