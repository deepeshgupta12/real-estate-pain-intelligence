from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.retrieval import (
    RetrievalDocumentResponse,
    RetrievalIndexResponse,
    RetrievalSearchRequest,
    RetrievalSearchResult,
)
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/index/{run_id}", response_model=RetrievalIndexResponse)
def index_run_retrieval(
    run_id: int,
    db: Session = Depends(get_db),
) -> RetrievalIndexResponse:
    run, indexed_count = RetrievalService.index_run(db=db, run_id=run_id)
    return RetrievalIndexResponse(
        run_id=run.id,
        indexed_count=indexed_count,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("/{run_id}", response_model=list[RetrievalDocumentResponse])
def list_run_retrieval_documents(
    run_id: int,
    db: Session = Depends(get_db),
) -> list[RetrievalDocumentResponse]:
    return RetrievalService.list_run_documents(db=db, run_id=run_id)


@router.post("/search", response_model=list[RetrievalSearchResult])
def search_retrieval(
    payload: RetrievalSearchRequest,
    db: Session = Depends(get_db),
) -> list[RetrievalSearchResult]:
    results = RetrievalService.search(
        db=db,
        query=payload.query,
        top_k=payload.top_k,
        run_id=payload.run_id,
    )
    return [
        RetrievalSearchResult(
            retrieval_document_id=row.id,
            scrape_run_id=row.scrape_run_id,
            raw_evidence_id=row.raw_evidence_id,
            agent_insight_id=row.agent_insight_id,
            title=row.title,
            document_type=row.document_type,
            language_code=row.language_code,
            score=score,
            document_text=row.document_text,
            metadata_json=row.metadata_json,
            created_at=row.created_at,
        )
        for row, score in results
    ]