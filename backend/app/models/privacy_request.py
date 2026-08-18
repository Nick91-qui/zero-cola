from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel
from app.models.enums import PrivacyRequestStatus, PrivacyRequestType


class PrivacyRequest(BaseModel):
    __tablename__ = "privacy_requests"
    __table_args__ = (
        Index("ix_privacy_requests_user_id", "user_id"),
        Index("ix_privacy_requests_status", "status"),
        Index("ix_privacy_requests_type", "request_type"),
        Index("ix_privacy_requests_created_at", "created_at"),
        Index(
            "ix_privacy_requests_pending_user_type",
            "user_id",
            "request_type",
            unique=True,
            sqlite_where=text("status = 'pending'"),
            postgresql_where=text("status = 'pending'"),
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_type: Mapped[PrivacyRequestType] = mapped_column(
        Enum(
            PrivacyRequestType,
            name="privacy_request_type",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    status: Mapped[PrivacyRequestStatus] = mapped_column(
        Enum(
            PrivacyRequestStatus,
            name="privacy_request_status",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=PrivacyRequestStatus.PENDING,
        server_default=text("'pending'"),
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="privacy_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_id], backref="created_privacy_requests")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id], backref="reviewed_privacy_requests")
