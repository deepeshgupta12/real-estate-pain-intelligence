from datetime import datetime
from typing import Any

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


class RunQueueSummaryResponse(BaseModel):
    run_id: int
    source_name: str
    target_brand: str
    status: str
    pipeline_stage: str
    items_discovered: int
    items_processed: int
    last_heartbeat_at: datetime | None
    orchestrator_notes: str | None
    heartbeat_age_seconds: int | None
    is_stale: bool
    health_label: str
    latest_event_type: str | None
    latest_event_at: datetime | None
    latest_event_message: str | None


class RunDiagnosticsLatestEvent(BaseModel):
    id: int
    event_type: str
    stage: str
    status: str
    message: str
    created_at: datetime


class RunStageTimelineEntry(BaseModel):
    stage: str
    first_event_at: datetime
    last_event_at: datetime
    latest_status: str
    event_count: int
    duration_seconds: int


class RunFailureSnapshot(BaseModel):
    failed: bool
    error_message: str | None
    failed_at: datetime | None
    failed_stage: str | None
    failed_event_message: str | None
    last_successful_stage: str | None


class RunDiagnosticsResponse(BaseModel):
    run_id: int
    source_name: str
    target_brand: str
    status: str
    pipeline_stage: str
    trigger_mode: str
    items_discovered: int
    items_processed: int
    started_at: datetime | None
    last_heartbeat_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    error_message: str | None
    orchestrator_notes: str | None
    heartbeat_age_seconds: int | None
    is_stale: bool
    health_label: str
    total_events: int
    latest_event: RunDiagnosticsLatestEvent | None
    stage_timeline: list[RunStageTimelineEntry]
    readiness_checks: dict[str, bool]
    readiness_counts: dict[str, int]
    failure_snapshot: RunFailureSnapshot
    metadata: dict[str, Any] = Field(default_factory=dict)