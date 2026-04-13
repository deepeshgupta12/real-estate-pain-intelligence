from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.orchestrator import (
    OrchestratorDispatchResponse,
    OrchestratorFailRequest,
    OrchestratorProgressRequest,
    RunDiagnosticsResponse,
    RunQueueSummaryResponse,
)
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/dispatch/{run_id}", response_model=OrchestratorDispatchResponse)
def dispatch_run(run_id: int, db: Session = Depends(get_db)) -> OrchestratorDispatchResponse:
    run = OrchestratorService.dispatch_run(db, run_id)
    return OrchestratorDispatchResponse(
        run_id=run.id,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        trigger_mode=run.trigger_mode,
        orchestrator_notes=run.orchestrator_notes,
        started_at=run.started_at,
        last_heartbeat_at=run.last_heartbeat_at,
        completed_at=run.completed_at,
    )


@router.post("/start/{run_id}", response_model=OrchestratorDispatchResponse)
def start_run(run_id: int, db: Session = Depends(get_db)) -> OrchestratorDispatchResponse:
    run = OrchestratorService.start_run(db, run_id)
    return OrchestratorDispatchResponse(
        run_id=run.id,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        trigger_mode=run.trigger_mode,
        orchestrator_notes=run.orchestrator_notes,
        started_at=run.started_at,
        last_heartbeat_at=run.last_heartbeat_at,
        completed_at=run.completed_at,
    )


@router.post("/progress/{run_id}", response_model=OrchestratorDispatchResponse)
def update_progress(
    run_id: int,
    payload: OrchestratorProgressRequest,
    db: Session = Depends(get_db),
) -> OrchestratorDispatchResponse:
    run = OrchestratorService.update_progress(
        db=db,
        run_id=run_id,
        pipeline_stage=payload.pipeline_stage,
        items_discovered=payload.items_discovered,
        items_processed=payload.items_processed,
        orchestrator_notes=payload.orchestrator_notes,
    )
    return OrchestratorDispatchResponse(
        run_id=run.id,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        trigger_mode=run.trigger_mode,
        orchestrator_notes=run.orchestrator_notes,
        started_at=run.started_at,
        last_heartbeat_at=run.last_heartbeat_at,
        completed_at=run.completed_at,
    )


@router.post("/complete/{run_id}", response_model=OrchestratorDispatchResponse)
def complete_run(run_id: int, db: Session = Depends(get_db)) -> OrchestratorDispatchResponse:
    run = OrchestratorService.complete_run(db, run_id)
    return OrchestratorDispatchResponse(
        run_id=run.id,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        trigger_mode=run.trigger_mode,
        orchestrator_notes=run.orchestrator_notes,
        started_at=run.started_at,
        last_heartbeat_at=run.last_heartbeat_at,
        completed_at=run.completed_at,
    )


@router.post("/fail/{run_id}", response_model=OrchestratorDispatchResponse)
def fail_run(
    run_id: int,
    payload: OrchestratorFailRequest,
    db: Session = Depends(get_db),
) -> OrchestratorDispatchResponse:
    run = OrchestratorService.fail_run(
        db=db,
        run_id=run_id,
        error_message=payload.error_message,
        orchestrator_notes=payload.orchestrator_notes,
    )
    return OrchestratorDispatchResponse(
        run_id=run.id,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        trigger_mode=run.trigger_mode,
        orchestrator_notes=run.orchestrator_notes,
        started_at=run.started_at,
        last_heartbeat_at=run.last_heartbeat_at,
        completed_at=run.completed_at,
    )


@router.get("/queue", response_model=list[RunQueueSummaryResponse])
def list_active_queue(db: Session = Depends(get_db)) -> list[RunQueueSummaryResponse]:
    return OrchestratorService.list_active_queue_summaries(db)


@router.get("/diagnostics/{run_id}", response_model=RunDiagnosticsResponse)
def get_run_diagnostics(run_id: int, db: Session = Depends(get_db)) -> RunDiagnosticsResponse:
    diagnostics = OrchestratorService.build_run_diagnostics(db=db, run_id=run_id)
    return RunDiagnosticsResponse(**diagnostics)