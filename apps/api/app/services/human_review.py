import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.human_review_item import HumanReviewItem
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.schemas.human_review import (
    HumanReviewBulkDecisionResponse,
    HumanReviewEvidenceSnapshot,
    HumanReviewInsightSnapshot,
    HumanReviewItemResponse,
    HumanReviewQueueSummaryResponse,
)
from app.services.final_hardening import FinalHardeningService
from app.services.orchestrator import OrchestratorService
from app.services.run_logger import get_run_logger, teardown_run_logger

logger = logging.getLogger(__name__)


class HumanReviewService:
    @staticmethod
    def _truncate_text(text: str | None, max_chars: int = 320) -> str | None:
        if not text:
            return None
        normalized = " ".join(text.split()).strip()
        if len(normalized) <= max_chars:
            return normalized
        return normalized[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _get_evidence_text(evidence: RawEvidence | None) -> str | None:
        if evidence is None:
            return None
        return (
            evidence.bridge_text
            or evidence.normalized_text
            or evidence.cleaned_text
            or evidence.raw_text
        )

    @staticmethod
    def _build_source_summary(
        insight: AgentInsight,
        evidence: RawEvidence | None,
    ) -> str:
        parts = [
            insight.pain_point_label or "",
            insight.pain_point_summary or "",
            insight.root_cause_hypothesis or "",
            insight.action_recommendation or "",
            HumanReviewService._truncate_text(HumanReviewService._get_evidence_text(evidence), 180)
            or "",
        ]
        return " | ".join(part.strip() for part in parts if part and part.strip())

    @staticmethod
    def _build_insight_snapshot(insight: AgentInsight | None) -> HumanReviewInsightSnapshot | None:
        if insight is None:
            return None

        metadata = insight.metadata_json or {}
        return HumanReviewInsightSnapshot(
            id=insight.id,
            raw_evidence_id=insight.raw_evidence_id,
            journey_stage=insight.journey_stage,
            pain_point_label=insight.pain_point_label,
            pain_point_summary=insight.pain_point_summary,
            taxonomy_cluster=insight.taxonomy_cluster,
            root_cause_hypothesis=insight.root_cause_hypothesis,
            competitor_label=insight.competitor_label,
            priority_label=insight.priority_label,
            action_recommendation=insight.action_recommendation,
            confidence_score=insight.confidence_score,
            insight_status=insight.insight_status,
            analysis_mode=metadata.get("analysis_mode"),
            llm_attempted=metadata.get("llm_attempted"),
            llm_used=metadata.get("llm_used"),
            metadata_json=metadata,
            created_at=insight.created_at,
        )

    @staticmethod
    def _build_evidence_snapshot(
        evidence: RawEvidence | None,
    ) -> HumanReviewEvidenceSnapshot | None:
        if evidence is None:
            return None

        return HumanReviewEvidenceSnapshot(
            id=evidence.id,
            source_name=evidence.source_name,
            platform_name=evidence.platform_name,
            content_type=evidence.content_type,
            source_url=evidence.source_url,
            published_at=evidence.published_at,
            language=evidence.language,
            resolved_language=evidence.resolved_language,
            normalization_status=evidence.normalization_status,
            multilingual_status=evidence.multilingual_status,
            evidence_excerpt=HumanReviewService._truncate_text(
                HumanReviewService._get_evidence_text(evidence),
                320,
            ),
            metadata_json=evidence.metadata_json or {},
            created_at=evidence.created_at,
        )

    @staticmethod
    def _build_review_item_response(
        item: HumanReviewItem,
        insight: AgentInsight | None = None,
        evidence: RawEvidence | None = None,
        include_details: bool = False,
    ) -> HumanReviewItemResponse:
        return HumanReviewItemResponse(
            id=item.id,
            scrape_run_id=item.scrape_run_id,
            agent_insight_id=item.agent_insight_id,
            review_status=item.review_status,
            reviewer_decision=item.reviewer_decision,
            reviewer_notes=item.reviewer_notes,
            source_summary=item.source_summary,
            priority_label=item.priority_label,
            metadata_json=item.metadata_json or {},
            reviewed_at=item.reviewed_at,
            created_at=item.created_at,
            insight_snapshot=HumanReviewService._build_insight_snapshot(insight)
            if include_details
            else None,
            evidence_snapshot=HumanReviewService._build_evidence_snapshot(evidence)
            if include_details
            else None,
        )

    @staticmethod
    def _load_insight_map(
        db: Session,
        items: list[HumanReviewItem],
    ) -> dict[int, AgentInsight]:
        insight_ids = [item.agent_insight_id for item in items]
        if not insight_ids:
            return {}
        rows = db.scalars(
            select(AgentInsight).where(AgentInsight.id.in_(insight_ids))
        ).all()
        return {row.id: row for row in rows}

    @staticmethod
    def _load_evidence_map_from_insights(
        db: Session,
        insights: list[AgentInsight],
    ) -> dict[int, RawEvidence]:
        evidence_ids = [insight.raw_evidence_id for insight in insights]
        if not evidence_ids:
            return {}
        rows = db.scalars(
            select(RawEvidence).where(RawEvidence.id.in_(evidence_ids))
        ).all()
        return {row.id: row for row in rows}

    @staticmethod
    def generate_review_queue(db: Session, run_id: int) -> tuple[ScrapeRun, int]:
        run_logger, fh = get_run_logger(run_id)
        run_logger.info("=== Review queue generation started for run %d ===", run_id)
        try:
            run = FinalHardeningService.ensure_run_not_failed(db, run_id)
            FinalHardeningService.ensure_insights_exist(db, run_id)

            insights = db.scalars(
                select(AgentInsight)
                .where(AgentInsight.scrape_run_id == run_id)
                .order_by(AgentInsight.id.asc())
            ).all()

            evidence_map = HumanReviewService._load_evidence_map_from_insights(db, insights)

            db.execute(delete(HumanReviewItem).where(HumanReviewItem.scrape_run_id == run_id))
            db.commit()

            run_logger.info("Generating review items for %d insights", len(insights))

            OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="human_review_queue_generation",
                orchestrator_notes="Human review queue generation started",
            )

            generated_count = 0

            for insight in insights:
                evidence = evidence_map.get(insight.raw_evidence_id)
                insight_metadata = insight.metadata_json or {}

                run_logger.debug(
                    "Review item: insight_id=%s pain=%s priority=%s source=%s",
                    insight.id, insight.pain_point_label, insight.priority_label,
                    evidence.source_name if evidence else "N/A",
                )

                item = HumanReviewItem(
                    scrape_run_id=run_id,
                    agent_insight_id=insight.id,
                    review_status="pending_review",
                    reviewer_decision=None,
                    reviewer_notes=None,
                    source_summary=HumanReviewService._build_source_summary(insight, evidence),
                    priority_label=insight.priority_label,
                    metadata_json={
                        "journey_stage": insight.journey_stage,
                        "taxonomy_cluster": insight.taxonomy_cluster,
                        "competitor_label": insight.competitor_label,
                        "confidence_score": insight.confidence_score,
                        "pain_point_label": insight.pain_point_label,
                        "analysis_mode": insight_metadata.get("analysis_mode"),
                        "llm_attempted": insight_metadata.get("llm_attempted"),
                        "llm_used": insight_metadata.get("llm_used"),
                        "raw_evidence_id": insight.raw_evidence_id,
                        "source_name": evidence.source_name if evidence else None,
                        "platform_name": evidence.platform_name if evidence else None,
                        "content_type": evidence.content_type if evidence else None,
                    },
                )
                db.add(item)
                generated_count += 1

            db.commit()

            run_logger.info(
                "=== Review queue complete for run %d — %d items generated ===",
                run_id, generated_count,
            )

            run = OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="human_review_queue_ready",
                items_processed=run.items_processed,
                orchestrator_notes=f"Human review queue generated: {generated_count} items",
            )

            return run, generated_count
        finally:
            teardown_run_logger(run_id, fh)

    @staticmethod
    def list_review_queue(
        db: Session,
        run_id: int | None = None,
        review_status: str | None = None,
        reviewer_decision: str | None = None,
        priority_label: str | None = None,
        analysis_mode: str | None = None,
        include_details: bool = False,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[HumanReviewItemResponse]:
        stmt = select(HumanReviewItem).order_by(HumanReviewItem.id.asc())

        if run_id is not None:
            stmt = stmt.where(HumanReviewItem.scrape_run_id == run_id)

        if review_status is not None:
            stmt = stmt.where(HumanReviewItem.review_status == review_status)

        if reviewer_decision is not None:
            stmt = stmt.where(HumanReviewItem.reviewer_decision == reviewer_decision)

        if priority_label is not None:
            stmt = stmt.where(HumanReviewItem.priority_label == priority_label)

        items = list(db.scalars(stmt).all())
        insight_map = HumanReviewService._load_insight_map(db, items)
        insight_rows = list(insight_map.values())
        evidence_map = HumanReviewService._load_evidence_map_from_insights(db, insight_rows)

        if analysis_mode is not None:
            filtered_items: list[HumanReviewItem] = []
            for item in items:
                insight = insight_map.get(item.agent_insight_id)
                current_mode = (insight.metadata_json or {}).get("analysis_mode") if insight else None
                if current_mode == analysis_mode:
                    filtered_items.append(item)
            items = filtered_items

        items = items[offset : offset + limit]

        responses: list[HumanReviewItemResponse] = []
        for item in items:
            insight = insight_map.get(item.agent_insight_id)
            evidence = evidence_map.get(insight.raw_evidence_id) if insight else None
            responses.append(
                HumanReviewService._build_review_item_response(
                    item=item,
                    insight=insight,
                    evidence=evidence,
                    include_details=include_details,
                )
            )
        return responses

    @staticmethod
    def build_review_summary(
        db: Session,
        run_id: int | None = None,
    ) -> HumanReviewQueueSummaryResponse:
        stmt = select(HumanReviewItem).order_by(HumanReviewItem.id.asc())
        if run_id is not None:
            stmt = stmt.where(HumanReviewItem.scrape_run_id == run_id)

        items = list(db.scalars(stmt).all())
        insight_map = HumanReviewService._load_insight_map(db, items)

        total_items = len(items)
        pending_review_count = sum(1 for item in items if item.review_status == "pending_review")
        reviewed_count = sum(1 for item in items if item.review_status == "reviewed")
        approved_count = sum(1 for item in items if item.reviewer_decision == "approved")
        rejected_count = sum(1 for item in items if item.reviewer_decision == "rejected")
        high_priority_count = sum(1 for item in items if item.priority_label == "high")

        llm_assisted_count = 0
        deterministic_count = 0

        for item in items:
            insight = insight_map.get(item.agent_insight_id)
            analysis_mode = (insight.metadata_json or {}).get("analysis_mode") if insight else None
            if analysis_mode == "llm_assisted":
                llm_assisted_count += 1
            elif analysis_mode in {"deterministic_only", "deterministic_fallback"}:
                deterministic_count += 1

        return HumanReviewQueueSummaryResponse(
            run_id=run_id,
            total_items=total_items,
            pending_review_count=pending_review_count,
            reviewed_count=reviewed_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            high_priority_count=high_priority_count,
            llm_assisted_count=llm_assisted_count,
            deterministic_count=deterministic_count,
        )

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
    def get_review_item_detail(
        db: Session,
        review_item_id: int,
    ) -> HumanReviewItemResponse:
        item = HumanReviewService.get_review_item_or_404(db, review_item_id)
        insight = db.get(AgentInsight, item.agent_insight_id)
        evidence = db.get(RawEvidence, insight.raw_evidence_id) if insight else None
        return HumanReviewService._build_review_item_response(
            item=item,
            insight=insight,
            evidence=evidence,
            include_details=True,
        )

    @staticmethod
    def _apply_decision(
        item: HumanReviewItem,
        reviewer_decision: str,
        reviewer_notes: str | None = None,
    ) -> None:
        item.review_status = "reviewed"
        item.reviewer_decision = reviewer_decision
        item.reviewer_notes = reviewer_notes
        item.reviewed_at = datetime.now(timezone.utc)

    @staticmethod
    def approve_item(
        db: Session,
        review_item_id: int,
        reviewer_notes: str | None = None,
    ) -> HumanReviewItemResponse:
        item = HumanReviewService.get_review_item_or_404(db, review_item_id)
        HumanReviewService._apply_decision(
            item=item,
            reviewer_decision="approved",
            reviewer_notes=reviewer_notes,
        )
        db.commit()
        db.refresh(item)
        return HumanReviewService.get_review_item_detail(db=db, review_item_id=item.id)

    @staticmethod
    def reject_item(
        db: Session,
        review_item_id: int,
        reviewer_notes: str | None = None,
    ) -> HumanReviewItemResponse:
        item = HumanReviewService.get_review_item_or_404(db, review_item_id)
        HumanReviewService._apply_decision(
            item=item,
            reviewer_decision="rejected",
            reviewer_notes=reviewer_notes,
        )
        db.commit()
        db.refresh(item)
        return HumanReviewService.get_review_item_detail(db=db, review_item_id=item.id)

    @staticmethod
    def bulk_decide(
        db: Session,
        item_ids: list[int],
        reviewer_decision: str,
        reviewer_notes: str | None = None,
    ) -> HumanReviewBulkDecisionResponse:
        deduped_ids = list(dict.fromkeys(item_ids))
        items = list(
            db.scalars(
                select(HumanReviewItem)
                .where(HumanReviewItem.id.in_(deduped_ids))
                .order_by(HumanReviewItem.id.asc())
            ).all()
        )

        found_ids = {item.id for item in items}
        missing_ids = [item_id for item_id in deduped_ids if item_id not in found_ids]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Human review items not found: {missing_ids}",
            )

        for item in items:
            HumanReviewService._apply_decision(
                item=item,
                reviewer_decision=reviewer_decision,
                reviewer_notes=reviewer_notes,
            )

        db.commit()

        return HumanReviewBulkDecisionResponse(
            updated_count=len(items),
            reviewer_decision=reviewer_decision,
            item_ids=deduped_ids,
        )