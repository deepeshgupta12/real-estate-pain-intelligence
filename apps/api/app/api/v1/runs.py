from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scrape_run import ScrapeRun
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
        started_at=payload.started_at,
        last_heartbeat_at=payload.last_heartbeat_at,
        completed_at=payload.completed_at,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("", response_model=list[ScrapeRunResponse])
def list_scrape_runs(db: Session = Depends(get_db)) -> list[ScrapeRun]:
    runs = db.scalars(select(ScrapeRun).order_by(ScrapeRun.id.desc())).all()
    return list(runs)


@router.get("/{run_id}", response_model=ScrapeRunResponse)
def get_scrape_run(run_id: int, db: Session = Depends(get_db)) -> ScrapeRun:
    run = db.get(ScrapeRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scrape run {run_id} not found",
        )
    return run