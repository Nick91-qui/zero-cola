from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.repositories.skill import SkillRepository
from app.schemas.skill import SkillCreate, SkillResponse

router = APIRouter()


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_skill(
    skill_in: SkillCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = SkillRepository(db)
    existing = repo.get_by_code(skill_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill with code '{skill_in.code}' already exists.",
        )
    return repo.create(skill_in)


@router.get("", response_model=List[SkillResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_skills(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = SkillRepository(db)
    return repo.get_all(skip=skip, limit=limit)
