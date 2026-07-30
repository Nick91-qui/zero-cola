from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PrivacyPolicyResponse(BaseModel):
    title: str
    version: str
    summary: str
    monitoring_events: list[str]
    data_categories: list[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataExportResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: dict[str, Any]
