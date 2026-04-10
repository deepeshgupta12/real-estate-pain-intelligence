from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentInsightResponse(BaseModel):
    id: int
    scrape_run_id: int
    raw_evidence_id: int
    journey_stage: str | None
    pain_point_label: str | None
    pain_point_summary: str | None
    taxonomy_cluster: str | None
    root_cause_hypothesis: str | None
    competitor_label: str | None
    priority_label: str | None
    action_recommendation: str | None
    confidence_score: str | None
    insight_status: str
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}