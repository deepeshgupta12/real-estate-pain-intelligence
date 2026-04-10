from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agent_insight import AgentInsightResponse
from app.schemas.intelligence import RunIntelligenceResponse
from app.services.intelligence import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/{run_id}", response_model=RunIntelligenceResponse)
def process_run_intelligence(
    run_id: int,
    db: Session = Depends(get_db),
) -> RunIntelligenceResponse:
    run, total, generated_count, failed_count = IntelligenceService.process_run(
        db=db,
        run_id=run_id,
    )
    return RunIntelligenceResponse(
        run_id=run.id,
        total_evidence=total,
        insights_generated=generated_count,
        failed_count=failed_count,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("/{run_id}", response_model=list[AgentInsightResponse])
def list_run_intelligence(
    run_id: int,
    db: Session = Depends(get_db),
) -> list[AgentInsightResponse]:
    return IntelligenceService.list_run_insights(db, run_id=run_id)