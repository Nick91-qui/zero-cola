from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SecurityEventCreate(BaseModel):
    event_type: str = Field(..., max_length=50)
    metadata: Optional[dict] = Field(default=None, alias="details")


class SecurityEventResponse(BaseModel):
    id: UUID
    attempt_id: UUID
    event_type: str
    metadata: Optional[dict] = Field(default=None, alias="details")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
