from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.security_event import SecurityEventCreate, SecurityEventResponse
from app.services.security_event import SecurityEventService

router = APIRouter()


@router.post(
    "/attempts/{attempt_id}/security-events",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_role(UserRole.STUDENT)
async def create_security_event(
    attempt_id: UUID,
    event_in: SecurityEventCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SecurityEventService(db)
    try:
        return service.create_event(
            attempt_id=attempt_id,
            current_user=current_user,
            event_type=event_in.event_type,
            metadata=event_in.metadata,
        )
    except PermissionError as exc:
        detail = str(exc)
        status_code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=detail)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/attempts/{attempt_id}/security-events", response_model=list[SecurityEventResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_security_events(
    attempt_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SecurityEventService(db)
    try:
        return service.list_events(attempt_id=attempt_id, current_user=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
