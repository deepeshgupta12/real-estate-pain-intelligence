from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.human_review_item import HumanReviewItem
from app.models.scrape_run import ScrapeRun
from app.services.final_hardening import FinalHardeningService
from app.services.orchestrator import OrchestratorService


class HumanReviewService:
    @staticmethod
    def generate_review_queue(db: Session, run_id: int) -> tuple[ScrapeRun, int]:
        run = FinalHardeningService.ensure_run_not_failed(db, run_id)
        FinalHardeningService.ensure_insights_exist(db, run_id)

        insights = db.scalars(
            select(AgentInsight)
            .where(AgentInsight.scrape_run_id == run_id)
            .order_by(AgentInsight.id.asc())
        ).all()

        db.execute(delete(HumanReviewItem).where(HumanReviewItem.scrape_run_id == run_id))
        db.commit()

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="human_review_queue_generation",
            orchestrator_notes="Human review queue generation started",
        )

        generated_count = 0

        for insight in insights:
            summary_parts = [
                insight.pain_point_label or "",
                insight.pain_point_summary or "",
                insight.root_cause_hypothesis or "",
                insight.action_recommendation or "",
            ]
            source_summary = " | ".join(part.strip() for part in summary_parts if part and part.strip())

            item = HumanReviewItem(
                scrape_run_id=run_id,
                agent_insight_id=insight.id,
                review_status="pending_review",
                reviewer_decision=None,
                reviewer_notes=None,
                source_summary=source_summary,
                priority_label=insight.priority_label,
                metadata_json={
                    "journey_stage": insight.journey_stage,
                    "taxonomy_cluster": insight.taxonomy_cluster,
                    "competitor_label": insight.competitor_label,
                    "confidence_score": insight.confidence_score,
                },
            )
            db.add(item)
            generated_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="human_review_queue_ready",
            items_processed=run.items_processed,
            orchestrator_notes="Human review queue generated successfully",
        )

        return run, generated_count

    @staticmethod
    def list_review_queue(
        db: Session,
        run_id: int | None = None,
        review_status: str | None = None,
    ) -> list[HumanReviewItem]:
        stmt = select(HumanReviewItem).order_by(HumanReviewItem.id.asc())

        if run_id is not None:
            stmt = stmt.where(HumanReviewItem.scrape_run_id == run_id)

        if review_status is not None:
            stmt = stmt.where(HumanReviewItem.review_status == review_status)

        rows = db.scalars(stmt).all()
        return list(rows)

    @staticmethod
    def get_review_item_or_404(db: Session, review_item_id: int) -> HumanReviewItem:
        item = db.get(HumanReviewItem, review_item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Human review item {review_item_id} not found",
            )
        return item

    @staticmethod
    def approve_item(
        db: Session,
        review_item_id: int,
        reviewer_notes: str | None = None,
    ) -> HumanReviewItem:
        item = HumanReviewService.get_review_item_or_404(db, review_item_id)
        item.review_status = "reviewed"
        item.reviewer_decision = "approved"
        item.reviewer_notes = reviewer_notes
        item.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def reject_item(
        db: Session,
        review_item_id: int,
        reviewer_notes: str | None = None,
    ) -> HumanReviewItem:
        item = HumanReviewService.get_review_item_or_404(db, review_item_id)
        item.review_status = "reviewed"
        item.reviewer_decision = "rejected"
        item.reviewer_notes = reviewer_notes
        item.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item