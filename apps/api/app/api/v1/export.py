from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.export_job import ExportJob
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
        file_size_bytes=payload.file_size_bytes,
        row_count=payload.row_count,
        artifact_metadata_json=payload.artifact_metadata_json,
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


@router.get("/download/{export_job_id}")
def download_export_file(
    export_job_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    job = db.get(ExportJob, export_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    if not job.file_path or not job.file_name:
        raise HTTPException(status_code=404, detail="Export file has not been generated yet")

    file_path = Path(job.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    media_type_map = {
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf",
    }
    media_type = media_type_map.get(job.export_format, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=job.file_name,
        media_type=media_type,
    )