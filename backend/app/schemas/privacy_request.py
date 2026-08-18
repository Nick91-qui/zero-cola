from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import PrivacyRequestStatus, PrivacyRequestType
from app.schemas.user import UserResponse


class PrivacyRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    requested_by_id: UUID | None
    request_type: PrivacyRequestType
    status: PrivacyRequestStatus
    reason: str | None
    reviewed_by_id: UUID | None
    reviewed_at: datetime | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime
    user: UserResponse
    reviewed_by: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)
