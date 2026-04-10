from datetime import datetime

from pydantic import BaseModel, Field


class OrchestratorDispatchResponse(BaseModel):
    run_id: int
    status: str
    pipeline_stage: str
    trigger_mode: str
    orchestrator_notes: str | None
    started_at: datetime | None
    last_heartbeat_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OrchestratorProgressRequest(BaseModel):
    pipeline_stage: str = Field(..., min_length=1, max_length=50)
    items_discovered: int | None = Field(default=None, ge=0)
    items_processed: int | None = Field(default=None, ge=0)
    orchestrator_notes: str | None = None


class OrchestratorFailRequest(BaseModel):
    error_message: str = Field(..., min_length=1)
    orchestrator_notes: str | None = None