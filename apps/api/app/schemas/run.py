import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# All valid source names — must match ScraperRegistry keys
ALLOWED_SOURCES: frozenset[str] = frozenset({"reddit", "youtube", "app_reviews", "x", "review_sites"})


class ScrapeRunCreateRequest(BaseModel):
    # Comma-separated list of one or more source names, e.g. "reddit" or
    # "reddit,youtube,app_reviews".  Each token is validated against ALLOWED_SOURCES.
    source_name: str = Field(..., min_length=1)
    target_brand: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="created", min_length=1, max_length=50)
    pipeline_stage: str = Field(default="created", min_length=1, max_length=50)
    trigger_mode: str = Field(default="manual", min_length=1, max_length=50)
    items_discovered: int = Field(default=0, ge=0)
    items_processed: int = Field(default=0, ge=0)
    error_message: str | None = None
    orchestrator_notes: str | None = None
    # Persisted user-authored context; never overwritten by the pipeline.
    session_notes: str | None = None
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
        """Accept a single source name or a comma-separated list of source names."""
        tokens = [t.strip() for t in v.split(",") if t.strip()]
        if not tokens:
            raise ValueError("source_name must contain at least one source")
        invalid = [t for t in tokens if t not in ALLOWED_SOURCES]
        if invalid:
            raise ValueError(
                f"Invalid source(s): {', '.join(invalid)}. "
                f"Allowed: {', '.join(sorted(ALLOWED_SOURCES))}"
            )
        # Normalise: deduplicate preserving order, rejoin
        seen: set[str] = set()
        deduped = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return ",".join(deduped)


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
    session_notes: str | None
    started_at: datetime | None
    last_heartbeat_at: datetime | None
    completed_at: datetime | None
    archived_at: datetime | None = None
    organization_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
