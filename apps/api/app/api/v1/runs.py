from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.scrape_run import ScrapeRun
from app.models.user import User
from app.schemas.run import ScrapeRunCreateRequest, ScrapeRunResponse

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post(
    "",
    response_model=ScrapeRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scrape_run(
    payload: ScrapeRunCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # JWT auth required  # noqa: ARG001
) -> ScrapeRun:
    run = ScrapeRun(
        source_name=payload.source_name,
        target_brand=payload.target_brand,
        status=payload.status,
        pipeline_stage=payload.pipeline_stage,
        trigger_mode=payload.trigger_mode,
        items_discovered=payload.items_discovered,
        items_processed=payload.items_processed,
        error_message=payload.error_message,
        orchestrator_notes=payload.orchestrator_notes,
        session_notes=payload.session_notes,
        started_at=payload.started_at,
        last_heartbeat_at=payload.last_heartbeat_at,
        completed_at=payload.completed_at,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("", response_model=dict[str, Any])
def list_scrape_runs(
    limit: int = Query(default=50, ge=1, le=200, description="Number of runs to return"),
    offset: int = Query(default=0, ge=0, description="Number of runs to skip"),
    include_archived: bool = Query(default=False, description="Include archived runs"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List scrape runs with pagination. By default excludes archived runs."""
    base_stmt = select(ScrapeRun)
    if not include_archived:
        base_stmt = base_stmt.where(ScrapeRun.archived_at.is_(None))

    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
    runs = db.scalars(
        base_stmt.order_by(ScrapeRun.id.desc()).limit(limit).offset(offset)
    ).all()
    return {
        "items": list(runs),
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{run_id}", response_model=ScrapeRunResponse)
def get_scrape_run(run_id: int, db: Session = Depends(get_db)) -> ScrapeRun:
    run = db.get(ScrapeRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scrape run {run_id} not found",
        )
    return run


@router.post("/{run_id}/archive", response_model=ScrapeRunResponse)
def archive_scrape_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ScrapeRun:
    """Archive a scrape run — hides it from default listings but preserves all data."""
    run = db.get(ScrapeRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")
    if run.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Run is already archived")
    run.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


@router.post("/{run_id}/unarchive", response_model=ScrapeRunResponse)
def unarchive_scrape_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> ScrapeRun:
    """Restore an archived run back to the active listing."""
    run = db.get(ScrapeRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")
    if run.archived_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Run is not archived")
    run.archived_at = None
    db.commit()
    db.refresh(run)
    return run