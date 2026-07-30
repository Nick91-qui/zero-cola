from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConsentCreate(BaseModel):
    consent_type: str = Field(..., max_length=100)
    purpose: str = Field(..., max_length=255)
    granted: bool = True
    policy_version: Optional[str] = Field(default=None, max_length=50)
    metadata: Optional[dict] = Field(default=None, alias="details")


class MonitoringConsentCreate(BaseModel):
    purpose: str = Field(default="online_exam_monitoring", max_length=255)
    granted: bool = True
    policy_version: Optional[str] = Field(default=None, max_length=50)
    metadata: Optional[dict] = Field(default=None, alias="details")


class ConsentResponse(BaseModel):
    id: UUID
    user_id: UUID
    consent_type: str
    purpose: str
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    policy_version: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, alias="details")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
