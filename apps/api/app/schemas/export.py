from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportGenerateRequest(BaseModel):
    export_formats: list[str] = Field(default_factory=lambda: ["csv", "json", "pdf"])


class ExportGenerateResponse(BaseModel):
    run_id: int
    generated_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class ExportDecisionRequest(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    export_notes: str | None = None


class ExportJobResponse(BaseModel):
    id: int
    scrape_run_id: int
    export_format: str
    export_status: str
    file_name: str | None
    file_path: str | None
    summary_json: dict[str, Any]
    export_notes: str | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}