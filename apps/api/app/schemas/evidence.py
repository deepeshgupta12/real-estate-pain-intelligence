from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawEvidenceCreateRequest(BaseModel):
    scrape_run_id: int
    source_name: str = Field(..., min_length=1, max_length=100)
    platform_name: str = Field(..., min_length=1, max_length=100)
    content_type: str = Field(..., min_length=1, max_length=50)
    external_id: str | None = None
    author_name: str | None = None
    source_url: str | None = None
    published_at: datetime | None = None
    raw_text: str = Field(..., min_length=1)
    cleaned_text: str | None = None
    normalized_text: str | None = None
    normalized_language: str | None = None
    normalization_status: str = Field(default="pending", min_length=1, max_length=50)
    normalization_hash: str | None = None
    language: str | None = None
    is_relevant: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class RawEvidenceResponse(BaseModel):
    id: int
    scrape_run_id: int
    source_name: str
    platform_name: str
    content_type: str
    external_id: str | None
    author_name: str | None
    source_url: str | None
    published_at: datetime | None
    raw_text: str
    cleaned_text: str | None
    normalized_text: str | None
    normalized_language: str | None
    normalization_status: str
    normalization_hash: str | None
    language: str | None
    is_relevant: bool
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}