from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.human_review_item import HumanReviewItem
from app.models.notion_sync_job import NotionSyncJob
from app.models.scrape_run import ScrapeRun
from app.services.final_hardening import FinalHardeningService
from app.services.orchestrator import OrchestratorService


class NotionSyncService:
    @staticmethod
    def generate_sync_jobs(db: Session, run_id: int) -> tuple[ScrapeRun, int]:
        run = FinalHardeningService.ensure_run_not_failed(db, run_id)
        FinalHardeningService.ensure_approved_reviews_exist(db, run_id)

        review_items = db.scalars(
            select(HumanReviewItem)
            .where(HumanReviewItem.scrape_run_id == run_id)
            .where(HumanReviewItem.reviewer_decision == "approved")
            .order_by(HumanReviewItem.id.asc())
        ).all()

        db.execute(delete(NotionSyncJob).where(NotionSyncJob.scrape_run_id == run_id))
        db.commit()

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="notion_sync_job_generation",
            orchestrator_notes="Notion sync job generation started",
        )

        generated_count = 0

        for item in review_items:
            payload = {
                "review_item_id": item.id,
                "review_status": item.review_status,
                "reviewer_decision": item.reviewer_decision,
                "reviewer_notes": item.reviewer_notes,
                "priority_label": item.priority_label,
                "source_summary": item.source_summary,
                "metadata_json": item.metadata_json,
            }

            job = NotionSyncJob(
                scrape_run_id=run_id,
                human_review_item_id=item.id,
                sync_status="pending_sync",
                destination_label="notion_database",
                notion_page_id=None,
                sync_payload_json=payload,
                sync_notes="Prepared for Notion sync",
            )
            db.add(job)
            generated_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="notion_sync_queue_ready",
            items_processed=run.items_processed,
            orchestrator_notes="Notion sync jobs generated successfully",
        )

        return run, generated_count

    @staticmethod
    def list_sync_jobs(
        db: Session,
        run_id: int | None = None,
        sync_status: str | None = None,
    ) -> list[NotionSyncJob]:
        stmt = select(NotionSyncJob).order_by(NotionSyncJob.id.asc())

        if run_id is not None:
            stmt = stmt.where(NotionSyncJob.scrape_run_id == run_id)

        if sync_status is not None:
            stmt = stmt.where(NotionSyncJob.sync_status == sync_status)

        rows = db.scalars(stmt).all()
        return list(rows)

    @staticmethod
    def get_sync_job_or_404(db: Session, sync_job_id: int) -> NotionSyncJob:
        job = db.get(NotionSyncJob, sync_job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notion sync job {sync_job_id} not found",
            )
        return job

    @staticmethod
    def mark_synced(
        db: Session,
        sync_job_id: int,
        notion_page_id: str | None = None,
        sync_notes: str | None = None,
    ) -> NotionSyncJob:
        job = NotionSyncService.get_sync_job_or_404(db, sync_job_id)
        job.sync_status = "synced"
        job.notion_page_id = notion_page_id
        job.sync_notes = sync_notes or "Marked as synced"
        job.synced_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def mark_failed(
        db: Session,
        sync_job_id: int,
        sync_notes: str | None = None,
    ) -> NotionSyncJob:
        job = NotionSyncService.get_sync_job_or_404(db, sync_job_id)
        job.sync_status = "failed"
        job.sync_notes = sync_notes or "Notion sync failed"
        db.commit()
        db.refresh(job)
        return job