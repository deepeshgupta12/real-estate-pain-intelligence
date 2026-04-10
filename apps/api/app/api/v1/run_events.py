from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.run_event import RunEventResponse
from app.services.run_events import RunEventService

router = APIRouter(prefix="/run-events", tags=["run-events"])


@router.get("", response_model=list[RunEventResponse])
def list_recent_events(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[RunEventResponse]:
    return RunEventService.list_recent_events(db, limit=limit)


@router.get("/{run_id}", response_model=list[RunEventResponse])
def list_events_for_run(run_id: int, db: Session = Depends(get_db)) -> list[RunEventResponse]:
    return RunEventService.list_events_for_run(db, scrape_run_id=run_id)