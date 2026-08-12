from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.schemas import UserCreate, UserResponse
from app.services.audit_log import AuditLogService
from app.services.auth import AuthService

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
@require_role(UserRole.ADMIN)
async def create_user(
    user_in: UserCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        created = service.register_user(user_in)
        AuditLogService(db).record(
            event_type="admin.user_create",
            user_id=current_user.id,
            metadata={"email": user_in.email, "role": user_in.role.value},
        )
        db.commit()
        return created
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/users/search", response_model=list[UserResponse])
@require_role(UserRole.ADMIN)
async def search_users(
    q: str = "",
    role: UserRole | None = None,
    limit: int = 10,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    return repo.search(query=q, role=role, limit=limit)
