import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.notion_client import NotionClient
from app.models.agent_insight import AgentInsight
from app.models.human_review_item import HumanReviewItem
from app.models.notion_sync_job import NotionSyncJob
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.final_hardening import FinalHardeningService
from app.services.orchestrator import OrchestratorService


class NotionSyncService:
    @staticmethod
    def _build_idempotency_key(run_id: int, review_item_id: int) -> str:
        return f"run:{run_id}:review:{review_item_id}"

    @staticmethod
    def _payload_hash(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _build_sync_payload(
        db: Session,
        *,
        run: ScrapeRun,
        review_item: HumanReviewItem,
    ) -> dict[str, Any]:
        insight = db.get(AgentInsight, review_item.agent_insight_id)
        if insight is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent insight {review_item.agent_insight_id} not found",
            )

        evidence = db.get(RawEvidence, insight.raw_evidence_id)
        if evidence is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Raw evidence {insight.raw_evidence_id} not found",
            )

        return {
            "run": {
                "id": run.id,
                "source_name": run.source_name,
                "target_brand": run.target_brand,
                "status": run.status,
                "pipeline_stage": run.pipeline_stage,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            },
            "human_review_item": {
                "id": review_item.id,
                "review_status": review_item.review_status,
                "reviewer_decision": review_item.reviewer_decision,
                "reviewer_notes": review_item.reviewer_notes,
                "source_summary": review_item.source_summary,
                "priority_label": review_item.priority_label,
                "metadata_json": review_item.metadata_json,
                "reviewed_at": review_item.reviewed_at.isoformat() if review_item.reviewed_at else None,
            },
            "agent_insight": {
                "id": insight.id,
                "journey_stage": insight.journey_stage,
                "pain_point_label": insight.pain_point_label,
                "pain_point_summary": insight.pain_point_summary,
                "taxonomy_cluster": insight.taxonomy_cluster,
                "root_cause_hypothesis": insight.root_cause_hypothesis,
                "competitor_label": insight.competitor_label,
                "priority_label": insight.priority_label,
                "action_recommendation": insight.action_recommendation,
                "confidence_score": insight.confidence_score,
                "metadata_json": insight.metadata_json,
            },
            "raw_evidence": {
                "id": evidence.id,
                "source_name": evidence.source_name,
                "platform_name": evidence.platform_name,
                "content_type": evidence.content_type,
                "source_url": evidence.source_url,
                "published_at": evidence.published_at.isoformat() if evidence.published_at else None,
                "fetched_at": evidence.fetched_at.isoformat() if evidence.fetched_at else None,
                "source_query": evidence.source_query,
                "parser_version": evidence.parser_version,
                "raw_text": evidence.raw_text,
                "cleaned_text": evidence.cleaned_text,
                "normalized_text": evidence.normalized_text,
                "bridge_text": evidence.bridge_text,
                "language": evidence.language,
                "resolved_language": evidence.resolved_language,
                "metadata_json": evidence.metadata_json,
            },
        }

    @staticmethod
    def _rich_text(content: str) -> list[dict[str, Any]]:
        if not content:
            return [{"type": "text", "text": {"content": "-"}}]
        trimmed = content[:1900]
        return [{"type": "text", "text": {"content": trimmed}}]

    @staticmethod
    def _paragraph_block(content: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": NotionSyncService._rich_text(content),
            },
        }

    @staticmethod
    def _title_text(payload: dict[str, Any]) -> str:
        settings = get_settings()
        brand = payload["run"]["target_brand"]
        label = payload["agent_insight"].get("pain_point_label") or "Pain Point"
        review_id = payload["human_review_item"]["id"]
        return f"{settings.notion_default_title_prefix} | {brand} | {label} | Review {review_id}"

    @staticmethod
    def _safe_select_name(value: str | None, fallback: str) -> str:
        cleaned = (value or "").strip()
        return cleaned if cleaned else fallback

    @staticmethod
    def _build_database_properties(payload: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()

        title = NotionSyncService._title_text(payload)
        status_value = NotionSyncService._safe_select_name(
            payload["human_review_item"].get("review_status"),
            "Not started",
        )
        priority_value = NotionSyncService._safe_select_name(
            payload["human_review_item"].get("priority_label"),
            "medium",
        )
        brand_value = NotionSyncService._safe_select_name(
            payload["run"].get("target_brand"),
            "Unknown",
        )
        source_value = NotionSyncService._safe_select_name(
            payload["raw_evidence"].get("source_name"),
            "Unknown",
        )
        decision_value = NotionSyncService._safe_select_name(
            payload["human_review_item"].get("reviewer_decision"),
            "approved",
        )

        return {
            settings.notion_title_property_name: {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title},
                    }
                ]
            },
            settings.notion_status_property_name: {
                "select": {"name": status_value},
            },
            settings.notion_priority_property_name: {
                "select": {"name": priority_value},
            },
            settings.notion_brand_property_name: {
                "select": {"name": brand_value},
            },
            settings.notion_source_property_name: {
                "select": {"name": source_value},
            },
            settings.notion_decision_property_name: {
                "select": {"name": decision_value},
            },
        }

    @staticmethod
    def _build_children_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
        sections = [
            (
                "Pain Point Summary",
                payload["agent_insight"].get("pain_point_summary")
                or payload["human_review_item"].get("source_summary")
                or "-",
            ),
            (
                "Root Cause Hypothesis",
                payload["agent_insight"].get("root_cause_hypothesis") or "-",
            ),
            (
                "Action Recommendation",
                payload["agent_insight"].get("action_recommendation") or "-",
            ),
            (
                "Raw Evidence",
                payload["raw_evidence"].get("normalized_text")
                or payload["raw_evidence"].get("cleaned_text")
                or payload["raw_evidence"].get("raw_text")
                or "-",
            ),
            (
                "Metadata",
                json.dumps(
                    {
                        "journey_stage": payload["agent_insight"].get("journey_stage"),
                        "taxonomy_cluster": payload["agent_insight"].get("taxonomy_cluster"),
                        "competitor_label": payload["agent_insight"].get("competitor_label"),
                        "confidence_score": payload["agent_insight"].get("confidence_score"),
                        "source_url": payload["raw_evidence"].get("source_url"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )[:1900],
            ),
        ]

        children: list[dict[str, Any]] = []
        for heading, body in sections:
            children.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": NotionSyncService._rich_text(heading),
                    },
                }
            )
            children.append(NotionSyncService._paragraph_block(body))
        return children

    @staticmethod
    def generate_sync_jobs(db: Session, run_id: int) -> tuple[ScrapeRun, int]:
        settings = get_settings()
        run = FinalHardeningService.ensure_run_not_failed(db, run_id)
        FinalHardeningService.ensure_approved_reviews_exist(db, run_id)

        review_items = db.scalars(
            select(HumanReviewItem)
            .where(HumanReviewItem.scrape_run_id == run_id)
            .where(HumanReviewItem.reviewer_decision == "approved")
            .order_by(HumanReviewItem.id.asc())
        ).all()

        existing_jobs = db.scalars(
            select(NotionSyncJob).where(NotionSyncJob.scrape_run_id == run_id)
        ).all()
        jobs_by_review_id = {job.human_review_item_id: job for job in existing_jobs}

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="notion_sync_job_generation",
            orchestrator_notes="Real Notion sync job generation started",
        )

        generated_count = 0

        for item in review_items:
            payload = NotionSyncService._build_sync_payload(db=db, run=run, review_item=item)
            payload_hash = NotionSyncService._payload_hash(payload)
            idempotency_key = NotionSyncService._build_idempotency_key(run_id=run_id, review_item_id=item.id)

            existing = jobs_by_review_id.get(item.id)
            if existing is not None and existing.sync_status == "synced" and existing.notion_page_id:
                existing.sync_payload_json = payload
                existing.sync_notes = "Already synced; payload refreshed without duplicate creation"
                existing.provider_response_json = existing.provider_response_json or {}
                continue

            if existing is not None:
                existing.sync_status = "queued"
                existing.destination_label = settings.notion_destination_label
                existing.notion_database_id = settings.notion_database_id
                existing.idempotency_key = idempotency_key
                existing.sync_payload_json = payload
                existing.sync_notes = f"Queued for real Notion sync ({payload_hash[:12]})"
                existing.last_error_message = None
                existing.last_attempted_at = None
                existing.provider_response_json = {}
                if existing.sync_status != "synced":
                    existing.notion_page_id = None
                generated_count += 1
                continue

            job = NotionSyncJob(
                scrape_run_id=run_id,
                human_review_item_id=item.id,
                sync_status="queued",
                destination_label=settings.notion_destination_label,
                notion_page_id=None,
                notion_database_id=settings.notion_database_id,
                idempotency_key=idempotency_key,
                retry_count=0,
                sync_payload_json=payload,
                provider_response_json={},
                sync_notes=f"Queued for real Notion sync ({payload_hash[:12]})",
                last_error_message=None,
                last_attempted_at=None,
                synced_at=None,
            )
            db.add(job)
            generated_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="notion_sync_queue_ready",
            items_processed=run.items_processed,
            orchestrator_notes="Real Notion sync jobs prepared successfully",
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
    def execute_sync_job(db: Session, sync_job_id: int) -> NotionSyncJob:
        settings = get_settings()
        job = NotionSyncService.get_sync_job_or_404(db, sync_job_id)

        if job.sync_status == "synced" and job.notion_page_id:
            return job

        if not settings.notion_enable_real_sync:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Real Notion sync is disabled. Set NOTION_ENABLE_REAL_SYNC=true to execute sync.",
            )

        if settings.notion_destination_mode == "database" and not settings.notion_database_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NOTION_DATABASE_ID is required when NOTION_DESTINATION_MODE=database",
            )

        if settings.notion_destination_mode == "page" and not settings.notion_parent_page_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NOTION_PARENT_PAGE_ID is required when NOTION_DESTINATION_MODE=page",
            )

        payload = job.sync_payload_json or {}
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Notion sync job {sync_job_id} has empty sync payload",
            )

        children = NotionSyncService._build_children_blocks(payload)
        client = NotionClient()

        job.sync_status = "retrying" if job.retry_count > 0 else "queued"
        job.last_attempted_at = datetime.now(timezone.utc)
        db.commit()

        try:
            if settings.notion_destination_mode == "database":
                response = client.create_database_page(
                    database_id=settings.notion_database_id or "",
                    properties=NotionSyncService._build_database_properties(payload),
                    children=children,
                )
                job.notion_database_id = settings.notion_database_id
            else:
                response = client.create_child_page(
                    parent_page_id=settings.notion_parent_page_id or "",
                    title=NotionSyncService._title_text(payload),
                    children=children,
                )
                job.notion_database_id = None

            notion_page_id = response.get("id")
            if not notion_page_id:
                raise RuntimeError("Notion response did not include a page id")

            job.sync_status = "synced"
            job.notion_page_id = notion_page_id
            job.provider_response_json = response
            job.sync_notes = "Real Notion sync completed successfully"
            job.last_error_message = None
            job.synced_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)
            return job

        except Exception as exc:
            job.retry_count += 1
            job.last_error_message = str(exc)
            job.provider_response_json = {"error": str(exc)}
            job.sync_notes = "Real Notion sync attempt failed"
            job.sync_status = (
                "retrying"
                if job.retry_count <= settings.notion_max_retries
                else "failed"
            )
            db.commit()
            db.refresh(job)
            return job

    @staticmethod
    def execute_sync_jobs_for_run(db: Session, run_id: int) -> tuple[ScrapeRun, dict[str, int]]:
        run = FinalHardeningService.ensure_run_not_failed(db, run_id)

        jobs = db.scalars(
            select(NotionSyncJob)
            .where(NotionSyncJob.scrape_run_id == run_id)
            .where(NotionSyncJob.sync_status.in_(["queued", "retrying", "failed"]))
            .order_by(NotionSyncJob.id.asc())
        ).all()

        if not jobs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run {run_id} has no queued or retryable Notion sync jobs",
            )

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="notion_sync_execution",
            orchestrator_notes="Real Notion sync execution started",
        )

        attempted_count = 0
        synced_count = 0
        failed_count = 0
        retrying_count = 0

        for job in jobs:
            attempted_count += 1
            result = NotionSyncService.execute_sync_job(db=db, sync_job_id=job.id)
            if result.sync_status == "synced":
                synced_count += 1
            elif result.sync_status == "failed":
                failed_count += 1
            elif result.sync_status == "retrying":
                retrying_count += 1

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="notion_sync_executed",
            items_processed=run.items_processed,
            orchestrator_notes=(
                "Real Notion sync execution finished "
                f"(attempted={attempted_count}, synced={synced_count}, failed={failed_count}, retrying={retrying_count})"
            ),
        )

        return run, {
            "attempted_count": attempted_count,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "retrying_count": retrying_count,
        }

    @staticmethod
    def mark_synced(
        db: Session,
        sync_job_id: int,
        notion_page_id: str | None = None,
        notion_database_id: str | None = None,
        sync_notes: str | None = None,
    ) -> NotionSyncJob:
        job = NotionSyncService.get_sync_job_or_404(db, sync_job_id)
        job.sync_status = "synced"
        job.notion_page_id = notion_page_id
        job.notion_database_id = notion_database_id or job.notion_database_id
        job.sync_notes = sync_notes or "Marked as synced"
        job.last_error_message = None
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