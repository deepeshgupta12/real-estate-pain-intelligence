from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.scrape_execution import ScrapeExecutionResponse
from app.services.scrape_executor import ScrapeExecutionService

router = APIRouter(prefix="/scrape-execution", tags=["scrape-execution"])


@router.get("/sources", response_model=list[str])
def list_supported_sources() -> list[str]:
    from app.scrapers.registry import ScraperRegistry

    return ScraperRegistry.list_supported_sources()


@router.post("/{run_id}", response_model=ScrapeExecutionResponse)
def execute_scrape_run(run_id: int, db: Session = Depends(get_db)) -> ScrapeExecutionResponse:
    try:
        run, persisted_count, deduplicated_count = ScrapeExecutionService.execute_run(db, run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return ScrapeExecutionResponse(
        run_id=run.id,
        source_name=run.source_name,
        target_brand=run.target_brand,
        status=run.status,
        pipeline_stage=run.pipeline_stage,
        items_discovered=run.items_discovered,
        items_processed=run.items_processed,
        persisted_evidence_count=persisted_count,
        deduplicated_count=deduplicated_count,
        orchestrator_notes=run.orchestrator_notes,
    )