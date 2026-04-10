from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.schemas.evidence import RawEvidenceCreateRequest, RawEvidenceResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])


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
        raw_text=payload.raw_text,
        cleaned_text=payload.cleaned_text,
        language=payload.language,
        is_relevant=payload.is_relevant,
        metadata_json=payload.metadata_json,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("", response_model=list[RawEvidenceResponse])
def list_raw_evidence(db: Session = Depends(get_db)) -> list[RawEvidence]:
    evidence_items = db.scalars(
        select(RawEvidence).order_by(RawEvidence.id.desc())
    ).all()
    return list(evidence_items)


@router.get("/{evidence_id}", response_model=RawEvidenceResponse)
def get_raw_evidence(evidence_id: int, db: Session = Depends(get_db)) -> RawEvidence:
    evidence = db.get(RawEvidence, evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw evidence {evidence_id} not found",
        )
    return evidence