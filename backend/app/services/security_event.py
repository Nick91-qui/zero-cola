from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.attempt import Attempt
from app.models.enums import AttemptStatus, UserRole
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.services.audit_log import AuditLogService
from app.services.consent import ConsentService

ALLOWED_SECURITY_EVENT_TYPES = {
    "visibilitychange",
    "blur",
    "focus",
    "fullscreen_enter",
    "fullscreen_exit",
}


class SecurityEventService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_log_service = AuditLogService(db)
        self.consent_service = ConsentService(db)

    def _require_attempt(self, attempt_id: UUID, current_user: User) -> Attempt:
        attempt = (
            self.db.query(Attempt)
            .options(joinedload(Attempt.exam))
            .filter(Attempt.id == attempt_id)
            .first()
        )
        if attempt is None:
            raise ValueError(f"Attempt {attempt_id} not found.")
        if current_user.role == UserRole.STUDENT:
            if attempt.student_id != current_user.id:
                raise PermissionError("Attempt does not belong to the authenticated student.")
        elif current_user.role == UserRole.TEACHER:
            if attempt.exam.teacher_id != current_user.id:
                raise PermissionError("Attempt does not belong to the authenticated teacher.")
        return attempt

    def create_event(
        self,
        *,
        attempt_id: UUID,
        current_user: User,
        event_type: str,
        metadata: dict | None = None,
    ) -> SecurityEvent:
        if current_user.role != UserRole.STUDENT:
            raise PermissionError("Only students may record monitoring events.")
        event_type = event_type.strip()
        if event_type not in ALLOWED_SECURITY_EVENT_TYPES:
            raise ValueError(f"Unsupported security event type: {event_type}")
        attempt = self._require_attempt(attempt_id, current_user)
        if attempt.status != AttemptStatus.IN_PROGRESS.value:
            raise PermissionError("Security events can only be recorded for in-progress attempts.")
        if not self.consent_service.has_granted(user_id=current_user.id, consent_type="monitoring"):
            raise PermissionError(
                "Monitoring consent is required before recording security events."
            )

        event = SecurityEvent(attempt_id=attempt.id, event_type=event_type, details=metadata)
        self.db.add(event)
        self.db.flush()
        self.audit_log_service.record(
            event_type="security_event.recorded",
            user_id=current_user.id,
            resource_type="security_event",
            resource_id=event.id,
            metadata={"attempt_id": str(attempt.id), "event_type": event_type},
        )
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_events(self, *, attempt_id: UUID, current_user: User) -> list[SecurityEvent]:
        attempt = self._require_attempt(attempt_id, current_user)
        if current_user.role == UserRole.STUDENT:
            raise PermissionError("Students cannot query security events.")
        if current_user.role == UserRole.TEACHER and attempt.exam.teacher_id != current_user.id:
            raise PermissionError("Attempt does not belong to the authenticated teacher.")
        return (
            self.db.query(SecurityEvent)
            .filter(SecurityEvent.attempt_id == attempt.id)
            .order_by(SecurityEvent.created_at.asc())
            .all()
        )
