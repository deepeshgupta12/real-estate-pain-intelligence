from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HumanReviewGenerateResponse(BaseModel):
    run_id: int
    generated_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class HumanReviewDecisionRequest(BaseModel):
    reviewer_notes: str | None = None


class HumanReviewItemResponse(BaseModel):
    id: int
    scrape_run_id: int
    agent_insight_id: int
    review_status: str
    reviewer_decision: str | None
    reviewer_notes: str | None
    source_summary: str | None
    priority_label: str | None
    metadata_json: dict[str, Any]
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}