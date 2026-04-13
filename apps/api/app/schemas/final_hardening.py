from pydantic import BaseModel


class FinalHardeningChecks(BaseModel):
    has_evidence: bool
    normalization_ready: bool
    multilingual_ready: bool
    intelligence_ready: bool
    retrieval_ready: bool
    human_review_ready: bool
    review_console_ready: bool
    notion_ready: bool
    export_ready: bool
    run_not_failed: bool


class FinalHardeningCounts(BaseModel):
    evidence_count: int
    normalized_count: int
    multilingual_count: int
    insight_count: int
    retrieval_count: int
    embedded_retrieval_count: int
    review_count: int
    pending_review_count: int
    approved_review_count: int
    rejected_review_count: int
    notion_sync_count: int
    export_count: int
    run_event_count: int


class RunReadinessResponse(BaseModel):
    run_id: int
    status: str
    pipeline_stage: str
    ready_for_finalization: bool
    checks: FinalHardeningChecks
    counts: FinalHardeningCounts


class SystemOverviewResponse(BaseModel):
    runs_total: int
    runs_completed: int
    runs_failed: int
    evidence_total: int
    insights_total: int
    retrieval_documents_total: int
    review_queue_total: int
    pending_review_total: int
    approved_review_total: int
    rejected_review_total: int
    notion_jobs_total: int
    export_jobs_total: int
    run_events_total: int


class ObservabilityOverviewResponse(BaseModel):
    runs_total: int
    active_queue_count: int
    stale_active_runs_count: int
    recent_failed_runs_count: int
    recent_events_count: int
    review_backlog_count: int
    run_events_total: int
    runs_by_status: dict[str, int]
    runs_by_stage: dict[str, int]