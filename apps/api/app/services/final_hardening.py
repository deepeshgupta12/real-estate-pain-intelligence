from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.export_job import ExportJob
from app.models.human_review_item import HumanReviewItem
from app.models.notion_sync_job import NotionSyncJob
from app.models.raw_evidence import RawEvidence
from app.models.retrieval_document import RetrievalDocument
from app.models.run_event import RunEvent
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService


class FinalHardeningService:
    @staticmethod
    def _count(db: Session, statement) -> int:
        value = db.scalar(statement)
        return int(value or 0)

    @staticmethod
    def ensure_run_not_failed(db: Session, run_id: int) -> ScrapeRun:
        run = OrchestratorService.get_run_or_404(db, run_id)
        if run.status == "failed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scrape run {run_id} is in failed state and cannot proceed",
            )
        return run

    @staticmethod
    def ensure_evidence_exists(db: Session, run_id: int) -> int:
        evidence_count = FinalHardeningService._count(
            db,
            select(func.count(RawEvidence.id)).where(RawEvidence.scrape_run_id == run_id),
        )
        if evidence_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run {run_id} has no evidence available for this operation",
            )
        return evidence_count

    @staticmethod
    def ensure_insights_exist(db: Session, run_id: int) -> int:
        insight_count = FinalHardeningService._count(
            db,
            select(func.count(AgentInsight.id)).where(AgentInsight.scrape_run_id == run_id),
        )
        if insight_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run {run_id} has no agent insights available for this operation",
            )
        return insight_count

    @staticmethod
    def ensure_approved_reviews_exist(db: Session, run_id: int) -> int:
        approved_count = FinalHardeningService._count(
            db,
            select(func.count(HumanReviewItem.id))
            .where(HumanReviewItem.scrape_run_id == run_id)
            .where(HumanReviewItem.reviewer_decision == "approved"),
        )
        if approved_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run {run_id} has no approved human review items available for this operation",
            )
        return approved_count

    @staticmethod
    def build_run_readiness(db: Session, run_id: int) -> dict[str, object]:
        run = OrchestratorService.get_run_or_404(db, run_id)

        evidence_count = FinalHardeningService._count(
            db,
            select(func.count(RawEvidence.id)).where(RawEvidence.scrape_run_id == run_id),
        )
        normalized_count = FinalHardeningService._count(
            db,
            select(func.count(RawEvidence.id))
            .where(RawEvidence.scrape_run_id == run_id)
            .where(RawEvidence.normalization_status == "normalized"),
        )
        multilingual_count = FinalHardeningService._count(
            db,
            select(func.count(RawEvidence.id))
            .where(RawEvidence.scrape_run_id == run_id)
            .where(RawEvidence.multilingual_status == "processed"),
        )
        insight_count = FinalHardeningService._count(
            db,
            select(func.count(AgentInsight.id)).where(AgentInsight.scrape_run_id == run_id),
        )
        retrieval_count = FinalHardeningService._count(
            db,
            select(func.count(RetrievalDocument.id)).where(RetrievalDocument.scrape_run_id == run_id),
        )
        embedded_retrieval_count = FinalHardeningService._count(
            db,
            select(func.count(RetrievalDocument.id))
            .where(RetrievalDocument.scrape_run_id == run_id)
            .where(RetrievalDocument.embedding_status == "embedded"),
        )
        review_count = FinalHardeningService._count(
            db,
            select(func.count(HumanReviewItem.id)).where(HumanReviewItem.scrape_run_id == run_id),
        )
        approved_review_count = FinalHardeningService._count(
            db,
            select(func.count(HumanReviewItem.id))
            .where(HumanReviewItem.scrape_run_id == run_id)
            .where(HumanReviewItem.reviewer_decision == "approved"),
        )
        notion_sync_count = FinalHardeningService._count(
            db,
            select(func.count(NotionSyncJob.id)).where(NotionSyncJob.scrape_run_id == run_id),
        )
        export_count = FinalHardeningService._count(
            db,
            select(func.count(ExportJob.id)).where(ExportJob.scrape_run_id == run_id),
        )
        run_event_count = FinalHardeningService._count(
            db,
            select(func.count(RunEvent.id)).where(RunEvent.scrape_run_id == run_id),
        )

        checks = {
            "has_evidence": evidence_count > 0,
            "normalization_ready": evidence_count > 0,
            "multilingual_ready": normalized_count > 0,
            "intelligence_ready": multilingual_count > 0 or normalized_count > 0,
            "retrieval_ready": embedded_retrieval_count > 0,
            "human_review_ready": insight_count > 0,
            "notion_ready": approved_review_count > 0,
            "export_ready": evidence_count > 0,
            "run_not_failed": run.status != "failed",
        }

        return {
            "run": run,
            "counts": {
                "evidence_count": evidence_count,
                "normalized_count": normalized_count,
                "multilingual_count": multilingual_count,
                "insight_count": insight_count,
                "retrieval_count": retrieval_count,
                "embedded_retrieval_count": embedded_retrieval_count,
                "review_count": review_count,
                "approved_review_count": approved_review_count,
                "notion_sync_count": notion_sync_count,
                "export_count": export_count,
                "run_event_count": run_event_count,
            },
            "checks": checks,
            "ready_for_finalization": all(checks.values()),
        }

    @staticmethod
    def build_system_overview(db: Session) -> dict[str, int]:
        return {
            "runs_total": FinalHardeningService._count(db, select(func.count(ScrapeRun.id))),
            "runs_completed": FinalHardeningService._count(
                db,
                select(func.count(ScrapeRun.id)).where(ScrapeRun.status == "completed"),
            ),
            "runs_failed": FinalHardeningService._count(
                db,
                select(func.count(ScrapeRun.id)).where(ScrapeRun.status == "failed"),
            ),
            "evidence_total": FinalHardeningService._count(db, select(func.count(RawEvidence.id))),
            "insights_total": FinalHardeningService._count(db, select(func.count(AgentInsight.id))),
            "retrieval_documents_total": FinalHardeningService._count(
                db,
                select(func.count(RetrievalDocument.id)),
            ),
            "review_queue_total": FinalHardeningService._count(
                db,
                select(func.count(HumanReviewItem.id)),
            ),
            "notion_jobs_total": FinalHardeningService._count(
                db,
                select(func.count(NotionSyncJob.id)),
            ),
            "export_jobs_total": FinalHardeningService._count(
                db,
                select(func.count(ExportJob.id)),
            ),
            "run_events_total": FinalHardeningService._count(db, select(func.count(RunEvent.id))),
        }