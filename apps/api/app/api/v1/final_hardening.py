from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.final_hardening import (
    ObservabilityOverviewResponse,
    RunReadinessResponse,
    SystemOverviewResponse,
)
from app.services.final_hardening import FinalHardeningService

router = APIRouter(prefix="/final-hardening", tags=["final-hardening"])


@router.get("/readiness/{run_id}", response_model=RunReadinessResponse)
def get_run_readiness(
    run_id: int,
    db: Session = Depends(get_db),
) -> RunReadinessResponse:
    summary = FinalHardeningService.build_run_readiness(db=db, run_id=run_id)
    run = summary["run"]
    return RunReadinessResponse(
        run_id=run.id,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        ready_for_finalization=bool(summary["ready_for_finalization"]),
        checks=summary["checks"],
        counts=summary["counts"],
    )


@router.get("/overview", response_model=SystemOverviewResponse)
def get_system_overview(db: Session = Depends(get_db)) -> SystemOverviewResponse:
    return SystemOverviewResponse(**FinalHardeningService.build_system_overview(db=db))


@router.get("/observability", response_model=ObservabilityOverviewResponse)
def get_observability_overview(db: Session = Depends(get_db)) -> ObservabilityOverviewResponse:
    return ObservabilityOverviewResponse(**FinalHardeningService.build_observability_overview(db=db))