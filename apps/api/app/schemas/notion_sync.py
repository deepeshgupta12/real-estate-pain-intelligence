from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotionSyncGenerateResponse(BaseModel):
    run_id: int
    generated_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class NotionSyncExecutionSummaryResponse(BaseModel):
    run_id: int
    attempted_count: int
    synced_count: int
    failed_count: int
    retrying_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class NotionSyncDecisionRequest(BaseModel):
    notion_page_id: str | None = None
    notion_database_id: str | None = None
    sync_notes: str | None = None


class NotionSyncJobResponse(BaseModel):
    id: int
    scrape_run_id: int
    human_review_item_id: int
    sync_status: str
    destination_label: str
    notion_page_id: str | None
    notion_database_id: str | None
    idempotency_key: str | None
    retry_count: int
    sync_payload_json: dict[str, Any]
    provider_response_json: dict[str, Any]
    sync_notes: str | None
    last_error_message: str | None
    last_attempted_at: datetime | None
    synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}