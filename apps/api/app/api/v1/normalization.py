from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.normalization import (
    EvidenceNormalizationSummaryResponse,
    RunNormalizationResponse,
)
from app.services.normalization import NormalizationService

router = APIRouter(prefix="/normalization", tags=["normalization"])


@router.post("/{run_id}", response_model=RunNormalizationResponse)
def normalize_run(run_id: int, db: Session = Depends(get_db)) -> RunNormalizationResponse:
    run, total, normalized_count, unresolved_count = NormalizationService.normalize_run(
        db=db,
        run_id=run_id,
    )
    return RunNormalizationResponse(
        run_id=run.id,
        total_evidence=total,
        normalized_count=normalized_count,
        pending_count=0 if unresolved_count == 0 else unresolved_count,
        failed_count=0,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("/{run_id}", response_model=list[EvidenceNormalizationSummaryResponse])
def list_run_normalization_summary(
    run_id: int,
    db: Session = Depends(get_db),
) -> list[EvidenceNormalizationSummaryResponse]:
    rows = NormalizationService.list_run_normalization_summary(db, run_id=run_id)
    return [
        EvidenceNormalizationSummaryResponse(
            evidence_id=row.id,
            normalization_status=row.normalization_status,
            normalized_language=row.normalized_language,
            normalization_hash=row.normalization_hash,
            normalized_text=row.normalized_text,
        )
        for row in rows
    ]