from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.schemas import UserResponse

router = APIRouter()


@router.get("/users/search", response_model=list[UserResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def search_users(
    q: str = "",
    role: UserRole | None = None,
    limit: int = 10,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    return repo.search(query=q, role=role, limit=limit)
