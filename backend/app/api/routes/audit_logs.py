from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log import AuditLogService

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
@require_role(UserRole.ADMIN)
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuditLogService(db)
    return service.list_logs(
        skip=skip,
        limit=limit,
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
    )
