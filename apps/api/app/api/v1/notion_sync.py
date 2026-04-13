from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notion_sync import (
    NotionSyncDecisionRequest,
    NotionSyncExecutionSummaryResponse,
    NotionSyncGenerateResponse,
    NotionSyncJobResponse,
)
from app.services.notion_sync import NotionSyncService

router = APIRouter(prefix="/notion-sync", tags=["notion-sync"])


@router.post("/generate/{run_id}", response_model=NotionSyncGenerateResponse)
def generate_notion_sync_jobs(
    run_id: int,
    db: Session = Depends(get_db),
) -> NotionSyncGenerateResponse:
    run, generated_count = NotionSyncService.generate_sync_jobs(db=db, run_id=run_id)
    return NotionSyncGenerateResponse(
        run_id=run.id,
        generated_count=generated_count,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.post("/execute/{sync_job_id}", response_model=NotionSyncJobResponse)
def execute_notion_sync_job(
    sync_job_id: int,
    db: Session = Depends(get_db),
) -> NotionSyncJobResponse:
    return NotionSyncService.execute_sync_job(db=db, sync_job_id=sync_job_id)


@router.post("/execute-run/{run_id}", response_model=NotionSyncExecutionSummaryResponse)
def execute_notion_sync_jobs_for_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> NotionSyncExecutionSummaryResponse:
    run, summary = NotionSyncService.execute_sync_jobs_for_run(db=db, run_id=run_id)
    return NotionSyncExecutionSummaryResponse(
        run_id=run.id,
        attempted_count=summary["attempted_count"],
        synced_count=summary["synced_count"],
        failed_count=summary["failed_count"],
        retrying_count=summary["retrying_count"],
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("", response_model=list[NotionSyncJobResponse])
def list_notion_sync_jobs(
    run_id: int | None = Query(default=None),
    sync_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[NotionSyncJobResponse]:
    return NotionSyncService.list_sync_jobs(
        db=db,
        run_id=run_id,
        sync_status=sync_status,
    )


@router.post("/mark-synced/{sync_job_id}", response_model=NotionSyncJobResponse)
def mark_notion_sync_job_synced(
    sync_job_id: int,
    payload: NotionSyncDecisionRequest,
    db: Session = Depends(get_db),
) -> NotionSyncJobResponse:
    return NotionSyncService.mark_synced(
        db=db,
        sync_job_id=sync_job_id,
        notion_page_id=payload.notion_page_id,
        notion_database_id=payload.notion_database_id,
        sync_notes=payload.sync_notes,
    )


@router.post("/mark-failed/{sync_job_id}", response_model=NotionSyncJobResponse)
def mark_notion_sync_job_failed(
    sync_job_id: int,
    payload: NotionSyncDecisionRequest,
    db: Session = Depends(get_db),
) -> NotionSyncJobResponse:
    return NotionSyncService.mark_failed(
        db=db,
        sync_job_id=sync_job_id,
        sync_notes=payload.sync_notes,
    )