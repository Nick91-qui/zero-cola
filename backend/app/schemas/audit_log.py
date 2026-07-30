from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    event_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    metadata: Optional[dict] = Field(default=None, alias="details")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
