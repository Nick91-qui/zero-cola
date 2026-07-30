from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.consent import Consent
from app.services.audit_log import AuditLogService


class ConsentService:
    DEFAULT_POLICY_VERSION = "step9-v1"

    def __init__(self, db: Session):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def upsert_consent(
        self,
        *,
        user_id: UUID,
        consent_type: str,
        purpose: str,
        granted: bool = True,
        policy_version: str | None = None,
        metadata: dict | None = None,
    ) -> Consent:
        consent_type = consent_type.strip().lower()
        policy_version = policy_version or self.DEFAULT_POLICY_VERSION
        now = datetime.now(timezone.utc)

        consent = (
            self.db.query(Consent)
            .filter(Consent.user_id == user_id, Consent.consent_type == consent_type)
            .first()
        )
        if consent is None:
            consent = Consent(
                user_id=user_id,
                consent_type=consent_type,
                purpose=purpose,
                granted=granted,
                granted_at=now if granted else None,
                revoked_at=None if granted else now,
                policy_version=policy_version,
                details=metadata,
            )
            self.db.add(consent)
        else:
            consent.purpose = purpose
            consent.granted = granted
            consent.policy_version = policy_version
            consent.details = metadata
            if granted:
                consent.granted_at = now
                consent.revoked_at = None
            else:
                consent.revoked_at = now
                if consent.granted_at is None:
                    consent.granted_at = None
        self.db.flush()
        self.audit_log_service.record(
            event_type="consent.updated" if granted else "consent.revoked",
            user_id=user_id,
            resource_type="consent",
            metadata={
                "consent_type": consent_type,
                "purpose": purpose,
                "granted": granted,
                "policy_version": policy_version,
                **({"metadata": metadata} if metadata is not None else {}),
            },
        )
        return consent

    def revoke_consent(
        self,
        *,
        user_id: UUID,
        consent_type: str,
        purpose: str | None = None,
        policy_version: str | None = None,
        metadata: dict | None = None,
    ) -> Consent:
        existing = self.get_consent(user_id=user_id, consent_type=consent_type)
        if existing is None:
            purpose = purpose or consent_type
        else:
            purpose = purpose or existing.purpose
            metadata = metadata if metadata is not None else existing.details
        return self.upsert_consent(
            user_id=user_id,
            consent_type=consent_type,
            purpose=purpose or consent_type,
            granted=False,
            policy_version=policy_version or (existing.policy_version if existing else None),
            metadata=metadata,
        )

    def get_consent(self, *, user_id: UUID, consent_type: str) -> Consent | None:
        return (
            self.db.query(Consent)
            .filter(
                Consent.user_id == user_id,
                Consent.consent_type == consent_type.strip().lower(),
            )
            .first()
        )

    def get_consents(self, *, user_id: UUID) -> list[Consent]:
        return (
            self.db.query(Consent)
            .filter(Consent.user_id == user_id)
            .order_by(Consent.created_at.desc())
            .all()
        )

    def has_granted(self, *, user_id: UUID, consent_type: str) -> bool:
        consent = self.get_consent(user_id=user_id, consent_type=consent_type)
        return bool(consent and consent.granted)
