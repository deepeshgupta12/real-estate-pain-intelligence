from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RetrievalIndexResponse(BaseModel):
    run_id: int
    indexed_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class RetrievalSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    run_id: int | None = None


class RetrievalSearchResult(BaseModel):
    retrieval_document_id: int
    scrape_run_id: int
    raw_evidence_id: int
    agent_insight_id: int | None
    title: str | None
    document_type: str
    language_code: str | None
    score: float
    document_text: str
    metadata_json: dict[str, Any]
    created_at: datetime


class RetrievalDocumentResponse(BaseModel):
    id: int
    scrape_run_id: int
    raw_evidence_id: int
    agent_insight_id: int | None
    title: str | None
    document_text: str
    document_type: str
    language_code: str | None
    retrieval_status: str
    token_count: int
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}