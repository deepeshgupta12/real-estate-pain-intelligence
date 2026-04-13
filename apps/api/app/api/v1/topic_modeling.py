"""
Topic modeling API endpoints.

GET  /api/v1/topic-modeling/{run_id}          — full topic analysis for a run
GET  /api/v1/topic-modeling/{run_id}/clusters — lightweight cluster summary
GET  /api/v1/topic-modeling/seed-clusters     — list of available seed clusters
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.topic_modeling import TopicModelingService, REAL_ESTATE_PAIN_SEEDS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/topic-modeling", tags=["topic-modeling"])


@router.get("/seed-clusters")
def list_seed_clusters() -> dict:
    """Return the list of predefined pain-point seed clusters."""
    return {
        "seed_clusters": REAL_ESTATE_PAIN_SEEDS,
        "total": len(REAL_ESTATE_PAIN_SEEDS),
    }


@router.get("/{run_id}")
def run_topic_modeling(run_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Run full topic modeling pipeline for a scrape run.
    Returns seed clusters, ML topics, and diversity metrics.
    """
    try:
        result = TopicModelingService.run_topic_modeling(db, run_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Topic modeling failed for run %s: %s", run_id, exc)
        raise HTTPException(status_code=500, detail="Topic modeling failed") from exc


@router.get("/{run_id}/clusters")
def get_cluster_summary(run_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Return a lightweight cluster summary for dashboard widgets.
    Faster than the full topic modeling endpoint.
    """
    try:
        clusters = TopicModelingService.get_cluster_summary(db, run_id)
        return {"run_id": run_id, "clusters": clusters, "total": len(clusters)}
    except Exception as exc:
        logger.error("Cluster summary failed for run %s: %s", run_id, exc)
        raise HTTPException(status_code=500, detail="Cluster summary failed") from exc
