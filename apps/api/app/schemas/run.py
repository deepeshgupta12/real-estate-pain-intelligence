from datetime import datetime

from pydantic import BaseModel, Field


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