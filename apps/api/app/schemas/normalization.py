from pydantic import BaseModel


class RunNormalizationResponse(BaseModel):
    run_id: int
    total_evidence: int
    normalized_count: int
    pending_count: int
    failed_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class EvidenceNormalizationSummaryResponse(BaseModel):
    evidence_id: int
    normalization_status: str
    normalized_language: str | None
    normalization_hash: str | None
    normalized_text: str | None