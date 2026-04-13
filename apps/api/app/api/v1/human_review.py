from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.human_review import (
    HumanReviewBulkDecisionRequest,
    HumanReviewBulkDecisionResponse,
    HumanReviewDecisionRequest,
    HumanReviewGenerateResponse,
    HumanReviewItemResponse,
    HumanReviewQueueSummaryResponse,
)
from app.services.human_review import HumanReviewService

router = APIRouter(prefix="/human-review", tags=["human-review"])


@router.post("/generate/{run_id}", response_model=HumanReviewGenerateResponse)
def generate_human_review_queue(
    run_id: int,
    db: Session = Depends(get_db),
) -> HumanReviewGenerateResponse:
    run, generated_count = HumanReviewService.generate_review_queue(db=db, run_id=run_id)
    return HumanReviewGenerateResponse(
        run_id=run.id,
        generated_count=generated_count,
        pipeline_stage=run.pipeline_stage,
        status=run.status,
        orchestrator_notes=run.orchestrator_notes,
    )


@router.get("/summary", response_model=HumanReviewQueueSummaryResponse)
def get_human_review_summary(
    run_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> HumanReviewQueueSummaryResponse:
    return HumanReviewService.build_review_summary(db=db, run_id=run_id)


@router.get("/detail/{review_item_id}", response_model=HumanReviewItemResponse)
def get_human_review_detail(
    review_item_id: int,
    db: Session = Depends(get_db),
) -> HumanReviewItemResponse:
    return HumanReviewService.get_review_item_detail(db=db, review_item_id=review_item_id)


@router.get("", response_model=list[HumanReviewItemResponse])
def list_human_review_queue(
    run_id: int | None = Query(default=None),
    review_status: str | None = Query(default=None),
    reviewer_decision: str | None = Query(default=None),
    priority_label: str | None = Query(default=None),
    analysis_mode: str | None = Query(default=None),
    include_details: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[HumanReviewItemResponse]:
    return HumanReviewService.list_review_queue(
        db=db,
        run_id=run_id,
        review_status=review_status,
        reviewer_decision=reviewer_decision,
        priority_label=priority_label,
        analysis_mode=analysis_mode,
        include_details=include_details,
        limit=limit,
        offset=offset,
    )


@router.post("/approve/{review_item_id}", response_model=HumanReviewItemResponse)
def approve_review_item(
    review_item_id: int,
    payload: HumanReviewDecisionRequest,
    db: Session = Depends(get_db),
) -> HumanReviewItemResponse:
    return HumanReviewService.approve_item(
        db=db,
        review_item_id=review_item_id,
        reviewer_notes=payload.reviewer_notes,
    )


@router.post("/reject/{review_item_id}", response_model=HumanReviewItemResponse)
def reject_review_item(
    review_item_id: int,
    payload: HumanReviewDecisionRequest,
    db: Session = Depends(get_db),
) -> HumanReviewItemResponse:
    return HumanReviewService.reject_item(
        db=db,
        review_item_id=review_item_id,
        reviewer_notes=payload.reviewer_notes,
    )


@router.post("/bulk/approve", response_model=HumanReviewBulkDecisionResponse)
def bulk_approve_review_items(
    payload: HumanReviewBulkDecisionRequest,
    db: Session = Depends(get_db),
) -> HumanReviewBulkDecisionResponse:
    return HumanReviewService.bulk_decide(
        db=db,
        item_ids=payload.item_ids,
        reviewer_decision="approved",
        reviewer_notes=payload.reviewer_notes,
    )


@router.post("/bulk/reject", response_model=HumanReviewBulkDecisionResponse)
def bulk_reject_review_items(
    payload: HumanReviewBulkDecisionRequest,
    db: Session = Depends(get_db),
) -> HumanReviewBulkDecisionResponse:
    return HumanReviewService.bulk_decide(
        db=db,
        item_ids=payload.item_ids,
        reviewer_decision="rejected",
        reviewer_notes=payload.reviewer_notes,
    )