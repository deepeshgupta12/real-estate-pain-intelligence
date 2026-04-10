from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.human_review import (
    HumanReviewDecisionRequest,
    HumanReviewGenerateResponse,
    HumanReviewItemResponse,
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


@router.get("", response_model=list[HumanReviewItemResponse])
def list_human_review_queue(
    run_id: int | None = Query(default=None),
    review_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[HumanReviewItemResponse]:
    return HumanReviewService.list_review_queue(
        db=db,
        run_id=run_id,
        review_status=review_status,
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