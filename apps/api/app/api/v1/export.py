from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.export import (
    ExportDecisionRequest,
    ExportGenerateRequest,
    ExportGenerateResponse,
    ExportJobResponse,
)
from app.services.export import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/generate/{run_id}", response_model=ExportGenerateResponse)
def generate_export_jobs(
    run_id: int,
    payload: ExportGenerateRequest,
    db: Session = Depends(get_db),
) -> ExportGenerateResponse:
    run, generated_count = ExportService.generate_export_jobs(
        db=db,
        run_id=run_id,
        export_formats=payload.export_formats,
    )
    return ExportGenerateResponse(
        run_id=run.id,
        generated_count=generated_count,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("", response_model=list[ExportJobResponse])
def list_export_jobs(
    run_id: int | None = Query(default=None),
    export_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ExportJobResponse]:
    return ExportService.list_export_jobs(
        db=db,
        run_id=run_id,
        export_status=export_status,
    )


@router.post("/mark-completed/{export_job_id}", response_model=ExportJobResponse)
def mark_export_job_completed(
    export_job_id: int,
    payload: ExportDecisionRequest,
    db: Session = Depends(get_db),
) -> ExportJobResponse:
    return ExportService.mark_completed(
        db=db,
        export_job_id=export_job_id,
        file_name=payload.file_name,
        file_path=payload.file_path,
        export_notes=payload.export_notes,
    )


@router.post("/mark-failed/{export_job_id}", response_model=ExportJobResponse)
def mark_export_job_failed(
    export_job_id: int,
    payload: ExportDecisionRequest,
    db: Session = Depends(get_db),
) -> ExportJobResponse:
    return ExportService.mark_failed(
        db=db,
        export_job_id=export_job_id,
        export_notes=payload.export_notes,
    )