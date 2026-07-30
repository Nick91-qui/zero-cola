from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        event_type: str,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        metadata: dict | None = None,
        request: Request | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=metadata,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        user_id: UUID | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
    ) -> list[AuditLog]:
        query = self.db.query(AuditLog)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if event_type is not None:
            query = query.filter(AuditLog.event_type == event_type)
        if resource_type is not None:
            query = query.filter(AuditLog.resource_type == resource_type)
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
