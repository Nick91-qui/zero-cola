from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class SecurityEvent(BaseModel):
    __tablename__ = "security_events"
    __table_args__ = (
        Index("ix_security_events_attempt_id", "attempt_id"),
        Index("ix_security_events_event_type", "event_type"),
        Index("ix_security_events_created_at", "created_at"),
    )

    attempt_id: Mapped[UUID] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    attempt = relationship("Attempt", back_populates="security_events")
