import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ScrapeRunCreateRequest(BaseModel):
    source_name: str = Field(..., min_length=1, max_length=100)
    target_brand: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="created", min_length=1, max_length=50)
    pipeline_stage: str = Field(default="created", min_length=1, max_length=50)
    trigger_mode: str = Field(default="manual", min_length=1, max_length=50)
    items_discovered: int = Field(default=0, ge=0)
    items_processed: int = Field(default=0, ge=0)
    error_message: str | None = None
    orchestrator_notes: str | None = None
    started_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("target_brand")
    @classmethod
    def validate_target_brand(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("target_brand cannot be empty")
        if len(v) > 100:
            raise ValueError("target_brand must be 100 characters or less")
        if re.search(r'[<>"\';\\]', v):
            raise ValueError("target_brand contains invalid characters")
        return v

    @field_validator("source_name")
    @classmethod
    def validate_source_name(cls, v: str) -> str:
        allowed = {"reddit", "youtube", "app_reviews", "x_posts", "review_sites"}
        if v not in allowed:
            raise ValueError(f"source_name must be one of: {', '.join(sorted(allowed))}")
        return v


class ScrapeRunResponse(BaseModel):
    id: int
    source_name: str
    target_brand: str
    status: str
    pipeline_stage: str
    trigger_mode: str
    items_discovered: int
    items_processed: int
    error_message: str | None
    orchestrator_notes: str | None
    started_at: datetime | None
    last_heartbeat_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}