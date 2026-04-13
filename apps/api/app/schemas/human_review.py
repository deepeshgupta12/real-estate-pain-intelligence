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


class HumanReviewBulkDecisionRequest(BaseModel):
    item_ids: list[int] = Field(min_length=1)
    reviewer_notes: str | None = None


class HumanReviewInsightSnapshot(BaseModel):
    id: int
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
    analysis_mode: str | None
    llm_attempted: bool | None
    llm_used: bool | None
    metadata_json: dict[str, Any]
    created_at: datetime


class HumanReviewEvidenceSnapshot(BaseModel):
    id: int
    source_name: str
    platform_name: str
    content_type: str
    source_url: str | None
    published_at: datetime | None
    language: str | None
    resolved_language: str | None
    normalization_status: str
    multilingual_status: str
    evidence_excerpt: str | None
    metadata_json: dict[str, Any]
    created_at: datetime


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
    insight_snapshot: HumanReviewInsightSnapshot | None = None
    evidence_snapshot: HumanReviewEvidenceSnapshot | None = None

    model_config = {"from_attributes": True}


class HumanReviewQueueSummaryResponse(BaseModel):
    run_id: int | None
    total_items: int
    pending_review_count: int
    reviewed_count: int
    approved_count: int
    rejected_count: int
    high_priority_count: int
    llm_assisted_count: int
    deterministic_count: int


class HumanReviewBulkDecisionResponse(BaseModel):
    updated_count: int
    reviewer_decision: str
    item_ids: list[int]