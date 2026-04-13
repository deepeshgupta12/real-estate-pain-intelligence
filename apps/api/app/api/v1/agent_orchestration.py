"""
Agent orchestration API endpoints.

GET  /api/v1/agent-orchestration/status         — orchestrator capability status
POST /api/v1/agent-orchestration/analyse        — analyse single evidence text
POST /api/v1/agent-orchestration/analyse-batch  — analyse batch of evidence items
POST /api/v1/agent-orchestration/run/{run_id}   — run orchestration over a scrape run
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.raw_evidence import RawEvidence
from app.services.agent_orchestrator import AgentOrchestratorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-orchestration", tags=["agent-orchestration"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class SingleAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Evidence text to analyse")
    context: dict = Field(default_factory=dict, description="Optional context metadata")
    use_cache: bool = Field(True, description="Whether to use the response cache")


class BatchAnalysisItem(BaseModel):
    evidence_id: int | None = None
    text: str
    context: dict = Field(default_factory=dict)


class BatchAnalysisRequest(BaseModel):
    items: list[BatchAnalysisItem] = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def get_orchestrator_status() -> dict:
    """Return the current capability status of the agent orchestrator."""
    return AgentOrchestratorService.get_agent_status()


@router.post("/analyse")
def analyse_evidence(request: SingleAnalysisRequest) -> dict:
    """
    Run 5-agent orchestration pipeline on a single evidence text.
    Returns structured output from all agents.
    """
    try:
        result = AgentOrchestratorService.analyse(
            evidence_text=request.text,
            context=request.context,
            use_cache=request.use_cache,
        )
        return result
    except Exception as exc:
        logger.error("Agent analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {exc}") from exc


@router.post("/analyse-batch")
def analyse_batch(request: BatchAnalysisRequest) -> dict:
    """
    Run 5-agent orchestration pipeline on a batch of evidence texts.
    Returns structured outputs for all items.
    """
    items = [
        {
            "evidence_id": item.evidence_id,
            "text": item.text,
            "context": item.context,
        }
        for item in request.items
    ]
    try:
        results = AgentOrchestratorService.analyse_batch(items)
        return {
            "total": len(results),
            "results": results,
        }
    except Exception as exc:
        logger.error("Batch agent analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {exc}") from exc


@router.post("/run/{run_id}")
def orchestrate_run(
    run_id: int,
    max_items: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    """
    Run 5-agent orchestration pipeline over all evidence in a scrape run.
    Analyses up to `max_items` evidence items.
    """
    evidences = db.execute(
        select(RawEvidence).where(RawEvidence.run_id == run_id).limit(max_items)
    ).scalars().all()

    if not evidences:
        raise HTTPException(
            status_code=404,
            detail=f"No evidence found for run {run_id}",
        )

    items = []
    for ev in evidences:
        text = (
            ev.bridge_text
            or ev.normalized_text
            or ev.cleaned_text
            or ev.raw_text
            or ""
        ).strip()
        if len(text) < 5:
            continue
        items.append(
            {
                "evidence_id": ev.id,
                "text": text,
                "context": {
                    "source_name": ev.source_name,
                    "platform_name": ev.platform_name,
                    "resolved_language": ev.resolved_language or ev.language or "unknown",
                },
            }
        )

    try:
        results = AgentOrchestratorService.analyse_batch(items, max_items=max_items)
        return {
            "run_id": run_id,
            "total_evidence": len(evidences),
            "analysed": len(results),
            "results": results,
            "orchestrator_status": AgentOrchestratorService.get_agent_status(),
        }
    except Exception as exc:
        logger.error("Run orchestration failed for run %s: %s", run_id, exc)
        raise HTTPException(status_code=500, detail=f"Run orchestration failed: {exc}") from exc
