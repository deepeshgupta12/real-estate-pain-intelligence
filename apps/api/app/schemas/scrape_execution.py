from pydantic import BaseModel


class ScrapeExecutionResponse(BaseModel):
    run_id: int
    source_name: str
    target_brand: str
    status: str
    pipeline_stage: str
    items_discovered: int
    items_processed: int
    persisted_evidence_count: int
    deduplicated_count: int
    live_items_count: int
    stub_items_count: int
    live_fetch_enabled: bool
    fallback_to_stub_used: bool
    orchestrator_notes: str | None