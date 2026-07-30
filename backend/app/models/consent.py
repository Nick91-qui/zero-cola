from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class Consent(BaseModel):
    __tablename__ = "consents"
    __table_args__ = (
        UniqueConstraint("user_id", "consent_type", name="uq_consents_user_consent_type"),
        Index("ix_consents_user_id", "user_id"),
        Index("ix_consents_consent_type", "consent_type"),
        Index("ix_consents_granted", "granted"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    granted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    granted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    policy_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="consents")
