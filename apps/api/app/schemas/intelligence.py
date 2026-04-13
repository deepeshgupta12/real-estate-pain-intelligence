from pydantic import BaseModel


class RunIntelligenceResponse(BaseModel):
    run_id: int
    total_evidence: int
    insights_generated: int
    llm_generated_count: int
    deterministic_generated_count: int
    failed_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None