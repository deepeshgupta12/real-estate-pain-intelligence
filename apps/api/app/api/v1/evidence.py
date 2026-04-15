from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.schemas.evidence import RawEvidenceCreateRequest, RawEvidenceResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _hydrate_legacy_evidence_defaults(evidence: RawEvidence) -> RawEvidence:
    if evidence.raw_payload_json is None:
        evidence.raw_payload_json = {}
    if evidence.metadata_json is None:
        evidence.metadata_json = {}
    return evidence


@router.post(
    "",
    response_model=RawEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_raw_evidence(
    payload: RawEvidenceCreateRequest,
    db: Session = Depends(get_db),
) -> RawEvidence:
    run = db.get(ScrapeRun, payload.scrape_run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scrape run {payload.scrape_run_id} not found",
        )

    evidence = RawEvidence(
        scrape_run_id=payload.scrape_run_id,
        source_name=payload.source_name,
        platform_name=payload.platform_name,
        content_type=payload.content_type,
        external_id=payload.external_id,
        author_name=payload.author_name,
        source_url=payload.source_url,
        published_at=payload.published_at,
        fetched_at=payload.fetched_at,
        source_query=payload.source_query,
        parser_version=payload.parser_version,
        dedupe_key=payload.dedupe_key,
        raw_payload_json=payload.raw_payload_json or {},
        raw_text=payload.raw_text,
        cleaned_text=payload.cleaned_text,
        normalized_text=payload.normalized_text,
        normalized_language=payload.normalized_language,
        normalization_status=payload.normalization_status,
        normalization_hash=payload.normalization_hash,
        resolved_language=payload.resolved_language,
        language_family=payload.language_family,
        script_label=payload.script_label,
        multilingual_status=payload.multilingual_status,
        multilingual_notes=payload.multilingual_notes,
        bridge_text=payload.bridge_text,
        language=payload.language,
        is_relevant=payload.is_relevant,
        metadata_json=payload.metadata_json or {},
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return _hydrate_legacy_evidence_defaults(evidence)


@router.get("", response_model=dict[str, Any])
def list_raw_evidence(
    run_id: Optional[int] = Query(default=None, description="Filter by scrape run ID"),
    source_name: Optional[str] = Query(default=None, description="Filter by source name"),
    content_type: Optional[str] = Query(default=None, description="Filter by content type"),
    limit: int = Query(default=100, ge=1, le=500, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List raw evidence items with server-side pagination. Returns items + total count."""
    base_stmt = select(RawEvidence)
    if run_id is not None:
        base_stmt = base_stmt.where(RawEvidence.scrape_run_id == run_id)
    if source_name is not None:
        base_stmt = base_stmt.where(RawEvidence.source_name == source_name)
    if content_type is not None:
        base_stmt = base_stmt.where(RawEvidence.content_type == content_type)

    total = db.scalar(
        select(func.count()).select_from(base_stmt.subquery())
    ) or 0

    stmt = base_stmt.order_by(RawEvidence.id.desc()).limit(limit).offset(offset)
    evidence_items = db.scalars(stmt).all()

    updated = False
    for evidence in evidence_items:
        if evidence.raw_payload_json is None or evidence.metadata_json is None:
            _hydrate_legacy_evidence_defaults(evidence)
            updated = True

    if updated:
        db.commit()

    # Explicitly convert ORM objects to Pydantic schema instances.
    # response_model=dict[str, Any] does NOT auto-serialize ORM objects —
    # FastAPI only auto-converts when response_model is a Pydantic model directly.
    return {
        "items": [RawEvidenceResponse.model_validate(e) for e in evidence_items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{evidence_id}", response_model=RawEvidenceResponse)
def get_raw_evidence(evidence_id: int, db: Session = Depends(get_db)) -> RawEvidence:
    evidence = db.get(RawEvidence, evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw evidence {evidence_id} not found",
        )

    if evidence.raw_payload_json is None or evidence.metadata_json is None:
        _hydrate_legacy_evidence_defaults(evidence)
        db.commit()
        db.refresh(evidence)

    return evidence