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
    orchestrator_notes: str | None