from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunEventResponse(BaseModel):
    id: int
    scrape_run_id: int
    event_type: str
    stage: str
    status: str
    message: str
    payload_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class RunEventCreateRequest(BaseModel):
    scrape_run_id: int
    event_type: str = Field(..., min_length=1, max_length=100)
    stage: str = Field(..., min_length=1, max_length=100)
    status: str = Field(..., min_length=1, max_length=50)
    message: str = Field(..., min_length=1)
    payload_json: dict[str, Any] = Field(default_factory=dict)