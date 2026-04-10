from pydantic import BaseModel


class RunMultilingualResponse(BaseModel):
    run_id: int
    total_evidence: int
    processed_count: int
    pending_count: int
    failed_count: int
    pipeline_stage: str
    status: str
    orchestrator_notes: str | None


class EvidenceMultilingualSummaryResponse(BaseModel):
    evidence_id: int
    resolved_language: str | None
    language_family: str | None
    script_label: str | None
    multilingual_status: str
    multilingual_notes: str | None
    bridge_text: str | None