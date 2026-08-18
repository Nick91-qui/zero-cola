from datetime import datetime, timezone
from uuid import UUID, uuid4

import bcrypt
from sqlalchemy.orm import Session, joinedload

from app.models.attempt import Attempt
from app.models.audit_log import AuditLog
from app.models.consent import Consent
from app.models.exam import Exam
from app.models.grade import Grade
from app.models.enums import PrivacyRequestStatus, PrivacyRequestType
from app.models.privacy_request import PrivacyRequest
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.services.audit_log import AuditLogService


class PrivacyService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    @staticmethod
    def get_privacy_policy() -> dict:
        return {
            "title": "COLA-ZERO Privacy Policy",
            "version": "step9",
            "summary": (
                "COLA-ZERO records only the minimum academic and monitoring data required "
                "to operate online and OMR assessments."
            ),
            "monitoring_events": [
                "visibilitychange",
                "blur",
                "focus",
                "fullscreen_enter",
                "fullscreen_exit",
            ],
            "data_categories": [
                "account profile",
                "attempts and grades",
                "class memberships",
                "security events",
                "audit logs",
                "consents",
            ],
            "updated_at": datetime.now(timezone.utc),
        }

    def export_user_data(self, *, user_id: UUID) -> dict:
        user = (
            self.db.query(User)
            .options(
                joinedload(User.grades),
                joinedload(User.consents),
                joinedload(User.created_classes),
                joinedload(User.class_memberships),
            )
            .filter(User.id == user_id)
            .first()
        )
        if user is None:
            raise ValueError(f"User {user_id} not found.")

        attempts = (
            self.db.query(Attempt)
            .options(joinedload(Attempt.answers), joinedload(Attempt.exam))
            .filter(Attempt.student_id == user.id)
            .order_by(Attempt.created_at.desc())
            .all()
        )
        grades = self.db.query(Grade).filter(Grade.student_id == user.id).all()
        consents = self.db.query(Consent).filter(Consent.user_id == user.id).all()
        audit_logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user.id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )
        security_events = (
            self.db.query(SecurityEvent)
            .join(Attempt, Attempt.id == SecurityEvent.attempt_id)
            .filter(Attempt.student_id == user.id)
            .order_by(SecurityEvent.created_at.desc())
            .all()
        )
        authored_exams = (
            self.db.query(Exam)
            .filter(Exam.teacher_id == user.id)
            .order_by(Exam.created_at.desc())
            .all()
        )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "student_code": user.student_code,
                "is_active": user.is_active,
                "anonymized_at": user.anonymized_at,
            },
            "class_memberships": [
                {
                    "class_id": str(membership.class_id),
                    "student_id": str(membership.student_id),
                    "is_active": membership.is_active,
                    "archived_at": membership.archived_at,
                }
                for membership in user.class_memberships
            ],
            "created_classes": [
                {
                    "id": str(class_obj.id),
                    "name": class_obj.name,
                    "description": class_obj.description,
                    "is_active": class_obj.is_active,
                    "archived_at": class_obj.archived_at,
                }
                for class_obj in user.created_classes
            ],
            "authored_exams": [
                {
                    "id": str(exam.id),
                    "title": exam.title,
                    "status": exam.status,
                    "is_active": exam.is_active,
                }
                for exam in authored_exams
            ],
            "attempts": [
                {
                    "id": str(attempt.id),
                    "exam_id": str(attempt.exam_id),
                    "status": attempt.status,
                    "source": attempt.source,
                    "attempt_number": attempt.attempt_number,
                    "final_score": str(attempt.final_score),
                    "answers": [
                        {
                            "question_number": answer.question_number,
                            "answer_key_item_id": str(answer.answer_key_item_id)
                            if answer.answer_key_item_id
                            else None,
                            "selected_option": answer.selected_option,
                            "answered_at": answer.answered_at,
                        }
                        for answer in attempt.answers
                    ],
                }
                for attempt in attempts
            ],
            "grades": [
                {
                    "id": str(grade.id),
                    "source_type": grade.source_type.value,
                    "source_id": str(grade.source_id),
                    "score": str(grade.score),
                }
                for grade in grades
            ],
            "security_events": [
                {
                    "id": str(event.id),
                    "attempt_id": str(event.attempt_id),
                    "event_type": event.event_type,
                    "metadata": event.details,
                    "created_at": event.created_at,
                }
                for event in security_events
            ],
            "audit_logs": [
                {
                    "id": str(log.id),
                    "event_type": log.event_type,
                    "resource_type": log.resource_type,
                    "resource_id": str(log.resource_id) if log.resource_id else None,
                    "metadata": log.details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at,
                }
                for log in audit_logs
            ],
            "consents": [
                {
                    "id": str(consent.id),
                    "consent_type": consent.consent_type,
                    "purpose": consent.purpose,
                    "granted": consent.granted,
                    "granted_at": consent.granted_at,
                    "revoked_at": consent.revoked_at,
                    "policy_version": consent.policy_version,
                    "metadata": consent.details,
                }
                for consent in consents
            ],
        }

    def _get_privacy_request(self, request_id: UUID | str) -> PrivacyRequest | None:
        if isinstance(request_id, str):
            request_id = UUID(request_id)
        return (
            self.db.query(PrivacyRequest)
            .options(joinedload(PrivacyRequest.user), joinedload(PrivacyRequest.reviewed_by))
            .filter(PrivacyRequest.id == request_id)
            .first()
        )

    def request_anonymization(
        self,
        *,
        user_id: UUID | str,
        requested_by_id: UUID | str | None = None,
        reason: str | None = None,
    ) -> PrivacyRequest:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        if isinstance(requested_by_id, str):
            requested_by_id = UUID(requested_by_id)

        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError(f"User {user_id} not found.")
        if user.anonymized_at is not None:
            raise ValueError(f"User {user_id} is already anonymized.")

        existing_request = (
            self.db.query(PrivacyRequest)
            .options(joinedload(PrivacyRequest.user), joinedload(PrivacyRequest.reviewed_by))
            .filter(
                PrivacyRequest.user_id == user.id,
                PrivacyRequest.request_type == PrivacyRequestType.ANONYMIZATION,
                PrivacyRequest.status == PrivacyRequestStatus.PENDING,
            )
            .first()
        )
        if existing_request is not None:
            return existing_request

        request = PrivacyRequest(
            user_id=user.id,
            requested_by_id=requested_by_id or user.id,
            request_type=PrivacyRequestType.ANONYMIZATION,
            status=PrivacyRequestStatus.PENDING,
            reason=reason,
        )
        self.db.add(request)
        self.db.flush()
        self.audit_log_service.record(
            event_type="lgpd.anonymization_requested",
            user_id=user.id,
            resource_type="privacy_request",
            resource_id=request.id,
            metadata={
                "email": user.email,
                "request_type": request.request_type.value,
                "status": request.status.value,
                "reason": reason,
            },
        )
        self.db.commit()
        refreshed_request = self._get_privacy_request(request.id)
        assert refreshed_request is not None
        return refreshed_request

    def list_privacy_requests(
        self,
        *,
        status: PrivacyRequestStatus | None = PrivacyRequestStatus.PENDING,
    ) -> list[PrivacyRequest]:
        query = self.db.query(PrivacyRequest).options(
            joinedload(PrivacyRequest.user),
            joinedload(PrivacyRequest.reviewed_by),
        )
        if status is not None:
            query = query.filter(PrivacyRequest.status == status)
        return query.order_by(PrivacyRequest.created_at.desc()).all()

    def get_my_privacy_request(self, *, user_id: UUID | str) -> PrivacyRequest | None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return (
            self.db.query(PrivacyRequest)
            .options(joinedload(PrivacyRequest.user), joinedload(PrivacyRequest.reviewed_by))
            .filter(
                PrivacyRequest.user_id == user_id,
                PrivacyRequest.request_type == PrivacyRequestType.ANONYMIZATION,
            )
            .order_by(PrivacyRequest.created_at.desc())
            .first()
        )

    def approve_privacy_request(
        self,
        *,
        request_id: UUID | str,
        reviewer: User,
    ) -> PrivacyRequest:
        request = self._get_privacy_request(request_id)
        if request is None:
            raise ValueError(f"Privacy request {request_id} not found.")
        if request.status != PrivacyRequestStatus.PENDING:
            raise ValueError(f"Privacy request {request_id} is not pending.")

        request.status = PrivacyRequestStatus.APPROVED
        request.reviewed_by_id = reviewer.id
        request.reviewed_at = datetime.now(timezone.utc)
        request.resolution_note = "approved"
        self.audit_log_service.record(
            event_type="admin.user_delete_approved",
            user_id=reviewer.id,
            resource_type="privacy_request",
            resource_id=request.id,
            metadata={
                "email": request.user.email,
                "request_type": request.request_type.value,
                "status": request.status.value,
            },
        )
        anonymized_user = self.anonymize_user(user_id=request.user_id, record_request_event=False)
        self.audit_log_service.record(
            event_type="admin.user_deleted",
            user_id=reviewer.id,
            resource_type="user",
            resource_id=request.user_id,
            metadata={
                "email": request.user.email,
                "role": request.user.role.value,
                "is_active": False,
                "anonymized_at": anonymized_user.anonymized_at.isoformat()
                if anonymized_user.anonymized_at
                else None,
            },
        )
        self.db.commit()
        refreshed_request = self._get_privacy_request(request.id)
        assert refreshed_request is not None
        return refreshed_request

    def reject_privacy_request(
        self,
        *,
        request_id: UUID | str,
        reviewer: User,
        resolution_note: str | None = None,
    ) -> PrivacyRequest:
        request = self._get_privacy_request(request_id)
        if request is None:
            raise ValueError(f"Privacy request {request_id} not found.")
        if request.status != PrivacyRequestStatus.PENDING:
            raise ValueError(f"Privacy request {request_id} is not pending.")

        request.status = PrivacyRequestStatus.REJECTED
        request.reviewed_by_id = reviewer.id
        request.reviewed_at = datetime.now(timezone.utc)
        request.resolution_note = resolution_note
        self.audit_log_service.record(
            event_type="admin.user_delete_rejected",
            user_id=reviewer.id,
            resource_type="privacy_request",
            resource_id=request.id,
            metadata={
                "email": request.user.email,
                "request_type": request.request_type.value,
                "status": request.status.value,
                "resolution_note": resolution_note,
            },
        )
        self.db.commit()
        refreshed_request = self._get_privacy_request(request.id)
        assert refreshed_request is not None
        return refreshed_request

    def anonymize_user(self, *, user_id: UUID | str, record_request_event: bool = True) -> User:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise ValueError(f"User {user_id} not found.")

        if user.anonymized_at is not None:
            return user

        anonymized_email = f"anonymized-{user.id.hex[:12]}@example.com"
        random_password = uuid4().hex
        user.email = anonymized_email
        user.password_hash = bcrypt.hashpw(random_password.encode(), bcrypt.gensalt()).decode()
        user.student_code = None
        user.is_active = False
        user.anonymized_at = datetime.now(timezone.utc)

        consents = self.db.query(Consent).filter(Consent.user_id == user.id).all()
        now = datetime.now(timezone.utc)
        for consent in consents:
            consent.granted = False
            consent.revoked_at = now

        if record_request_event:
            self.audit_log_service.record(
                event_type="lgpd.anonymization_requested",
                user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                metadata={"email": anonymized_email},
            )
        self.db.commit()
        self.db.refresh(user)
        return user
