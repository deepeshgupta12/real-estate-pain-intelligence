from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.multilingual import (
    EvidenceMultilingualSummaryResponse,
    RunMultilingualResponse,
)
from app.services.multilingual import MultilingualService

router = APIRouter(prefix="/multilingual", tags=["multilingual"])


@router.post("/{run_id}", response_model=RunMultilingualResponse)
def process_multilingual_run(run_id: int, db: Session = Depends(get_db)) -> RunMultilingualResponse:
    run, total, processed_count, unresolved_count = MultilingualService.process_run(
        db=db,
        run_id=run_id,
    )
    return RunMultilingualResponse(
        run_id=run.id,
        total_evidence=total,
        processed_count=processed_count,
        pending_count=0 if unresolved_count == 0 else unresolved_count,
        failed_count=0,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("/{run_id}", response_model=list[EvidenceMultilingualSummaryResponse])
def list_run_multilingual_summary(
    run_id: int,
    db: Session = Depends(get_db),
) -> list[EvidenceMultilingualSummaryResponse]:
    rows = MultilingualService.list_run_multilingual_summary(db, run_id=run_id)
    return [
        EvidenceMultilingualSummaryResponse(
            evidence_id=row.id,
            resolved_language=row.resolved_language,
            language_family=row.language_family,
            script_label=row.script_label,
            multilingual_status=row.multilingual_status,
            multilingual_notes=row.multilingual_notes,
            bridge_text=row.bridge_text,
        )
        for row in rows
    ]