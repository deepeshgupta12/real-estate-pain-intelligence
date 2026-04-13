from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.run_event import RunEventResponse
from app.services.run_events import RunEventService

router = APIRouter(prefix="/run-events", tags=["run-events"])


@router.get("", response_model=list[RunEventResponse])
def list_recent_events(
    run_id: int | None = Query(default=None),
    event_type: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    newest_first: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> list[RunEventResponse]:
    return RunEventService.list_events(
        db=db,
        scrape_run_id=run_id,
        event_type=event_type,
        stage=stage,
        status=status,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
    )


@router.get("/{run_id}", response_model=list[RunEventResponse])
def list_events_for_run(
    run_id: int,
    event_type: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    newest_first: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[RunEventResponse]:
    return RunEventService.list_events(
        db=db,
        scrape_run_id=run_id,
        event_type=event_type,
        stage=stage,
        status=status,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
    )