"""Trending pain points API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.trending import TrendingService

router = APIRouter(prefix="/trending", tags=["trending"])


@router.get("/pain-points")
def get_trending_pain_points(
    limit: int = 20,
    cluster: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Get the top recurring pain points across all runs, sorted by frequency."""
    return TrendingService.get_top_trending(db=db, limit=limit, cluster=cluster)


@router.post("/update/{run_id}")
def update_fingerprints(run_id: int, db: Session = Depends(get_db)) -> dict:
    """Trigger fingerprint update for a completed intelligence run."""
    return TrendingService.update_fingerprints_for_run(db=db, run_id=run_id)
