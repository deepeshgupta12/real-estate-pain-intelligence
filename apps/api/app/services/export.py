import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent_insight import AgentInsight
from app.models.export_job import ExportJob
from app.models.human_review_item import HumanReviewItem
from app.models.notion_sync_job import NotionSyncJob
from app.models.raw_evidence import RawEvidence
from app.models.retrieval_document import RetrievalDocument
from app.models.scrape_run import ScrapeRun
from app.services.final_hardening import FinalHardeningService
from app.services.orchestrator import OrchestratorService


class ExportService:
    SUPPORTED_FORMATS = {"csv", "json", "pdf"}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _output_dir() -> Path:
        settings = get_settings()
        output_dir = Path(settings.export_output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @staticmethod
    def _serialize_datetime(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @staticmethod
    def _serialize_run(run: ScrapeRun) -> dict[str, Any]:
        return {
            "id": run.id,
            "source_name": run.source_name,
            "target_brand": run.target_brand,
            "status": run.status,
            "pipeline_stage": run.pipeline_stage,
            "trigger_mode": run.trigger_mode,
            "items_discovered": run.items_discovered,
            "items_processed": run.items_processed,
            "error_message": run.error_message,
            "orchestrator_notes": run.orchestrator_notes,
            "session_notes": getattr(run, "session_notes", None),
            "started_at": ExportService._serialize_datetime(run.started_at),
            "last_heartbeat_at": ExportService._serialize_datetime(run.last_heartbeat_at),
            "completed_at": ExportService._serialize_datetime(run.completed_at),
            "created_at": ExportService._serialize_datetime(run.created_at),
            "updated_at": ExportService._serialize_datetime(run.updated_at),
        }

    @staticmethod
    def _serialize_evidence(row: RawEvidence) -> dict[str, Any]:
        return {
            "id": row.id,
            "scrape_run_id": row.scrape_run_id,
            "source_name": row.source_name,
            "platform_name": row.platform_name,
            "content_type": row.content_type,
            "external_id": row.external_id,
            "author_name": row.author_name,
            "source_url": row.source_url,
            "published_at": ExportService._serialize_datetime(row.published_at),
            "fetched_at": ExportService._serialize_datetime(row.fetched_at),
            "source_query": row.source_query,
            "parser_version": row.parser_version,
            "dedupe_key": row.dedupe_key,
            "raw_payload_json": row.raw_payload_json or {},
            "raw_text": row.raw_text,
            "cleaned_text": row.cleaned_text,
            "normalized_text": row.normalized_text,
            "normalized_language": row.normalized_language,
            "normalization_status": row.normalization_status,
            "normalization_hash": row.normalization_hash,
            "resolved_language": row.resolved_language,
            "language_family": row.language_family,
            "script_label": row.script_label,
            "multilingual_status": row.multilingual_status,
            "multilingual_notes": row.multilingual_notes,
            "bridge_text": row.bridge_text,
            "language": row.language,
            "is_relevant": row.is_relevant,
            "metadata_json": row.metadata_json or {},
            "created_at": ExportService._serialize_datetime(row.created_at),
        }

    @staticmethod
    def _serialize_insight(row: AgentInsight) -> dict[str, Any]:
        return {
            "id": row.id,
            "scrape_run_id": row.scrape_run_id,
            "raw_evidence_id": row.raw_evidence_id,
            "journey_stage": row.journey_stage,
            "pain_point_label": row.pain_point_label,
            "pain_point_summary": row.pain_point_summary,
            "taxonomy_cluster": row.taxonomy_cluster,
            "root_cause_hypothesis": row.root_cause_hypothesis,
            "competitor_label": row.competitor_label,
            "priority_label": row.priority_label,
            "action_recommendation": row.action_recommendation,
            "confidence_score": row.confidence_score,
            "insight_status": row.insight_status,
            "metadata_json": row.metadata_json or {},
            "created_at": ExportService._serialize_datetime(row.created_at),
        }

    @staticmethod
    def _serialize_retrieval_document(row: RetrievalDocument) -> dict[str, Any]:
        return {
            "id": row.id,
            "scrape_run_id": row.scrape_run_id,
            "raw_evidence_id": row.raw_evidence_id,
            "agent_insight_id": row.agent_insight_id,
            "title": row.title,
            "document_text": row.document_text,
            "document_type": row.document_type,
            "language_code": row.language_code,
            "retrieval_status": row.retrieval_status,
            "token_count": row.token_count,
            "metadata_json": row.metadata_json or {},
            "created_at": ExportService._serialize_datetime(row.created_at),
        }

    @staticmethod
    def _serialize_review_item(row: HumanReviewItem) -> dict[str, Any]:
        return {
            "id": row.id,
            "scrape_run_id": row.scrape_run_id,
            "agent_insight_id": row.agent_insight_id,
            "review_status": row.review_status,
            "reviewer_decision": row.reviewer_decision,
            "reviewer_notes": row.reviewer_notes,
            "source_summary": row.source_summary,
            "priority_label": row.priority_label,
            "metadata_json": row.metadata_json or {},
            "reviewed_at": ExportService._serialize_datetime(row.reviewed_at),
            "created_at": ExportService._serialize_datetime(row.created_at),
        }

    @staticmethod
    def _serialize_notion_job(row: NotionSyncJob) -> dict[str, Any]:
        return {
            "id": row.id,
            "scrape_run_id": row.scrape_run_id,
            "human_review_item_id": row.human_review_item_id,
            "sync_status": row.sync_status,
            "destination_label": row.destination_label,
            "notion_page_id": row.notion_page_id,
            "sync_payload_json": row.sync_payload_json or {},
            "sync_notes": row.sync_notes,
            "synced_at": ExportService._serialize_datetime(row.synced_at),
            "created_at": ExportService._serialize_datetime(row.created_at),
        }

    @staticmethod
    def _load_run_export_bundle(db: Session, run_id: int) -> dict[str, Any]:
        run = OrchestratorService.get_run_or_404(db, run_id)

        evidence_rows = list(
            db.scalars(
                select(RawEvidence)
                .where(RawEvidence.scrape_run_id == run_id)
                .order_by(RawEvidence.id.asc())
            ).all()
        )
        insight_rows = list(
            db.scalars(
                select(AgentInsight)
                .where(AgentInsight.scrape_run_id == run_id)
                .order_by(AgentInsight.id.asc())
            ).all()
        )
        retrieval_rows = list(
            db.scalars(
                select(RetrievalDocument)
                .where(RetrievalDocument.scrape_run_id == run_id)
                .order_by(RetrievalDocument.id.asc())
            ).all()
        )
        review_rows = list(
            db.scalars(
                select(HumanReviewItem)
                .where(HumanReviewItem.scrape_run_id == run_id)
                .order_by(HumanReviewItem.id.asc())
            ).all()
        )
        notion_rows = list(
            db.scalars(
                select(NotionSyncJob)
                .where(NotionSyncJob.scrape_run_id == run_id)
                .order_by(NotionSyncJob.id.asc())
            ).all()
        )

        payload = {
            "run": ExportService._serialize_run(run),
            "raw_evidence": [ExportService._serialize_evidence(row) for row in evidence_rows],
            "agent_insights": [ExportService._serialize_insight(row) for row in insight_rows],
            "retrieval_documents": [
                ExportService._serialize_retrieval_document(row) for row in retrieval_rows
            ],
            "human_review_items": [ExportService._serialize_review_item(row) for row in review_rows],
            "notion_sync_jobs": [ExportService._serialize_notion_job(row) for row in notion_rows],
        }

        pain_points = Counter(
            row.pain_point_label for row in insight_rows if row.pain_point_label
        ).most_common(5)
        priorities = Counter(
            row.priority_label for row in insight_rows if row.priority_label
        )
        review_statuses = Counter(row.review_status for row in review_rows if row.review_status)

        section_counts = {
            "raw_evidence": len(evidence_rows),
            "agent_insights": len(insight_rows),
            "retrieval_documents": len(retrieval_rows),
            "human_review_items": len(review_rows),
            "notion_sync_jobs": len(notion_rows),
        }

        summary = {
            "run_id": run_id,
            "target_brand": run.target_brand,
            "source_name": run.source_name,
            "section_counts": section_counts,
            "top_pain_points": [{"label": label, "count": count} for label, count in pain_points],
            "priority_breakdown": dict(priorities),
            "review_status_breakdown": dict(review_statuses),
        }

        return {
            "payload": payload,
            "summary": summary,
            "section_counts": section_counts,
        }

    @staticmethod
    def _build_csv_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
        evidence_rows = bundle["payload"]["raw_evidence"]
        insight_rows = bundle["payload"]["agent_insights"]
        review_rows = bundle["payload"]["human_review_items"]
        retrieval_rows = bundle["payload"]["retrieval_documents"]

        insight_by_evidence_id = {
            row["raw_evidence_id"]: row for row in insight_rows
        }
        review_by_insight_id = {
            row["agent_insight_id"]: row for row in review_rows
        }

        retrieval_count_by_evidence_id: dict[int, int] = {}
        for row in retrieval_rows:
            raw_evidence_id = row["raw_evidence_id"]
            retrieval_count_by_evidence_id[raw_evidence_id] = (
                retrieval_count_by_evidence_id.get(raw_evidence_id, 0) + 1
            )

        csv_rows: list[dict[str, Any]] = []

        for evidence in evidence_rows:
            insight = insight_by_evidence_id.get(evidence["id"])
            review = review_by_insight_id.get(insight["id"]) if insight else None

            csv_rows.append(
                {
                    "evidence_id": evidence["id"],
                    "scrape_run_id": evidence["scrape_run_id"],
                    "source_name": evidence["source_name"],
                    "platform_name": evidence["platform_name"],
                    "content_type": evidence["content_type"],
                    "author_name": evidence["author_name"],
                    "source_url": evidence["source_url"],
                    "published_at": evidence["published_at"],
                    "fetched_at": evidence["fetched_at"],
                    "source_query": evidence["source_query"],
                    "parser_version": evidence["parser_version"],
                    "dedupe_key": evidence["dedupe_key"],
                    "language": evidence["language"],
                    "resolved_language": evidence["resolved_language"],
                    "normalization_status": evidence["normalization_status"],
                    "multilingual_status": evidence["multilingual_status"],
                    "raw_text": evidence["raw_text"],
                    "cleaned_text": evidence["cleaned_text"],
                    "normalized_text": evidence["normalized_text"],
                    "bridge_text": evidence["bridge_text"],
                    "journey_stage": insight["journey_stage"] if insight else None,
                    "pain_point_label": insight["pain_point_label"] if insight else None,
                    "pain_point_summary": insight["pain_point_summary"] if insight else None,
                    "taxonomy_cluster": insight["taxonomy_cluster"] if insight else None,
                    "root_cause_hypothesis": insight["root_cause_hypothesis"] if insight else None,
                    "competitor_label": insight["competitor_label"] if insight else None,
                    "priority_label": insight["priority_label"] if insight else None,
                    "action_recommendation": insight["action_recommendation"] if insight else None,
                    "review_status": review["review_status"] if review else None,
                    "reviewer_decision": review["reviewer_decision"] if review else None,
                    "reviewer_notes": review["reviewer_notes"] if review else None,
                    "retrieval_match_count": retrieval_count_by_evidence_id.get(evidence["id"], 0),
                }
            )

        return csv_rows

    @staticmethod
    def _write_csv_export(run_id: int, bundle: dict[str, Any]) -> tuple[str, str, int, int, dict[str, Any]]:
        output_dir = ExportService._output_dir()
        generated_at = ExportService._now()
        timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
        file_name = f"run_{run_id}_{timestamp}.csv"
        file_path = output_dir / file_name

        rows = ExportService._build_csv_rows(bundle)
        fieldnames = list(rows[0].keys()) if rows else [
            "evidence_id",
            "scrape_run_id",
            "source_name",
            "platform_name",
            "content_type",
            "author_name",
            "source_url",
            "published_at",
            "fetched_at",
            "source_query",
            "parser_version",
            "dedupe_key",
            "language",
            "resolved_language",
            "normalization_status",
            "multilingual_status",
            "raw_text",
            "cleaned_text",
            "normalized_text",
            "bridge_text",
            "journey_stage",
            "pain_point_label",
            "pain_point_summary",
            "taxonomy_cluster",
            "root_cause_hypothesis",
            "competitor_label",
            "priority_label",
            "action_recommendation",
            "review_status",
            "reviewer_decision",
            "reviewer_notes",
            "retrieval_match_count",
        ]

        with file_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        file_size = file_path.stat().st_size
        artifact_metadata = {
            "export_scope": "run_level_flattened",
            "section_counts": bundle["section_counts"],
            "field_count": len(fieldnames),
        }
        return file_name, str(file_path), len(rows), file_size, artifact_metadata

    @staticmethod
    def _json_default_serializer(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    @staticmethod
    def _write_json_export(run_id: int, bundle: dict[str, Any]) -> tuple[str, str, int, int, dict[str, Any]]:
        output_dir = ExportService._output_dir()
        generated_at = ExportService._now()
        timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
        file_name = f"run_{run_id}_{timestamp}.json"
        file_path = output_dir / file_name

        export_payload = {
            "generated_at": generated_at.isoformat(),
            "summary": bundle["summary"],
            **bundle["payload"],
        }

        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(
                export_payload,
                json_file,
                ensure_ascii=False,
                indent=2,
                default=ExportService._json_default_serializer,
            )

        total_rows = sum(bundle["section_counts"].values())
        file_size = file_path.stat().st_size
        artifact_metadata = {
            "export_scope": "run_level_structured",
            "section_counts": bundle["section_counts"],
            "includes_summary": True,
        }
        return file_name, str(file_path), total_rows, file_size, artifact_metadata

    @staticmethod
    def _draw_wrapped_lines(pdf: canvas.Canvas, lines: list[str], x: int, y: int, line_height: int = 16) -> int:
        current_y = y
        for line in lines:
            pdf.drawString(x, current_y, line)
            current_y -= line_height
        return current_y

    @staticmethod
    def _write_pdf_export(run_id: int, bundle: dict[str, Any]) -> tuple[str, str, int, int, dict[str, Any]]:
        output_dir = ExportService._output_dir()
        generated_at = ExportService._now()
        timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
        file_name = f"run_{run_id}_{timestamp}.pdf"
        file_path = output_dir / file_name

        summary = bundle["summary"]
        run = bundle["payload"]["run"]
        pain_points = summary["top_pain_points"]
        priorities = summary["priority_breakdown"]
        reviews = summary["review_status_breakdown"]

        pdf = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4

        pdf.setTitle(f"Run {run_id} Executive Export Summary")

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(40, height - 50, "Real Estate Pain Intelligence Export Summary")

        pdf.setFont("Helvetica", 11)
        y = height - 85
        y = ExportService._draw_wrapped_lines(
            pdf,
            [
                f"Run ID: {run_id}",
                f"Brand: {run['target_brand']}",
                f"Source(s): {run['source_name']}",
                f"Generated At: {generated_at.isoformat()}",
                f"Pipeline Stage: {run['pipeline_stage']}",
                f"Run Status: {run['status']}",
                *(
                    [f"Session Notes: {run['session_notes']}"]
                    if run.get("session_notes")
                    else []
                ),
            ],
            40,
            y,
        )

        y -= 10
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Section Counts")
        y -= 20
        pdf.setFont("Helvetica", 11)
        y = ExportService._draw_wrapped_lines(
            pdf,
            [
                f"Raw Evidence: {summary['section_counts']['raw_evidence']}",
                f"Agent Insights: {summary['section_counts']['agent_insights']}",
                f"Retrieval Documents: {summary['section_counts']['retrieval_documents']}",
                f"Human Review Items: {summary['section_counts']['human_review_items']}",
                f"Notion Sync Jobs: {summary['section_counts']['notion_sync_jobs']}",
            ],
            40,
            y,
        )

        y -= 10
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Top Pain Points")
        y -= 20
        pdf.setFont("Helvetica", 11)
        if pain_points:
            pain_lines = [f"{item['label']}: {item['count']}" for item in pain_points]
        else:
            pain_lines = ["No pain point insights available yet."]
        y = ExportService._draw_wrapped_lines(pdf, pain_lines, 40, y)

        y -= 10
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Priority Breakdown")
        y -= 20
        pdf.setFont("Helvetica", 11)
        priority_lines = [f"{label}: {count}" for label, count in priorities.items()] or ["No priority labels available yet."]
        y = ExportService._draw_wrapped_lines(pdf, priority_lines, 40, y)

        y -= 10
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Review Status Breakdown")
        y -= 20
        pdf.setFont("Helvetica", 11)
        review_lines = [f"{label}: {count}" for label, count in reviews.items()] or ["No review activity available yet."]
        y = ExportService._draw_wrapped_lines(pdf, review_lines, 40, y)

        y -= 10
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Executive Summary")
        y -= 20
        pdf.setFont("Helvetica", 11)
        summary_lines = [
            (
                f"This export packages run-level evidence, normalized and multilingual-ready text, "
                f"agent insights, retrieval artifacts, human review state, and notion sync state "
                f"for brand {run['target_brand']}."
            ),
            (
                "The strongest observed themes are based on currently generated pain-point and "
                "priority labels and can be used directly by product, ops, and business teams."
            ),
        ]
        y = ExportService._draw_wrapped_lines(pdf, summary_lines, 40, y)

        pdf.showPage()
        pdf.save()

        total_rows = sum(bundle["section_counts"].values())
        file_size = file_path.stat().st_size
        artifact_metadata = {
            "export_scope": "run_level_executive_summary",
            "section_counts": bundle["section_counts"],
            "page_type": "executive_summary_pdf",
        }
        return file_name, str(file_path), total_rows, file_size, artifact_metadata

    @staticmethod
    def _generate_artifact(
        export_format: str,
        run_id: int,
        bundle: dict[str, Any],
    ) -> tuple[str, str, int, int, dict[str, Any]]:
        if export_format == "csv":
            return ExportService._write_csv_export(run_id, bundle)
        if export_format == "json":
            return ExportService._write_json_export(run_id, bundle)
        if export_format == "pdf":
            return ExportService._write_pdf_export(run_id, bundle)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {export_format}",
        )

    @staticmethod
    def generate_export_jobs(db: Session, run_id: int, export_formats: list[str]) -> tuple[ScrapeRun, int]:
        run = FinalHardeningService.ensure_run_not_failed(db, run_id)
        FinalHardeningService.ensure_evidence_exists(db, run_id)

        cleaned_formats: list[str] = []
        for fmt in export_formats:
            normalized = fmt.strip().lower()
            if normalized in ExportService.SUPPORTED_FORMATS and normalized not in cleaned_formats:
                cleaned_formats.append(normalized)

        if not cleaned_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one valid export format is required",
            )

        bundle = ExportService._load_run_export_bundle(db, run_id)

        db.execute(delete(ExportJob).where(ExportJob.scrape_run_id == run_id))
        db.commit()

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="export_generation",
            orchestrator_notes="Real export artifact generation started",
        )

        generated_count = 0
        failed_count = 0

        for export_format in cleaned_formats:
            generated_at = ExportService._now()
            try:
                file_name, file_path, row_count, file_size_bytes, artifact_metadata_json = (
                    ExportService._generate_artifact(export_format, run_id, bundle)
                )

                summary_json = {
                    **bundle["summary"],
                    "export_format": export_format,
                    "row_count": row_count,
                    "file_size_bytes": file_size_bytes,
                }

                job = ExportJob(
                    scrape_run_id=run_id,
                    export_format=export_format,
                    export_status="completed",
                    file_name=file_name,
                    file_path=file_path,
                    file_size_bytes=file_size_bytes,
                    row_count=row_count,
                    generated_at=generated_at,
                    summary_json=summary_json,
                    artifact_metadata_json=artifact_metadata_json,
                    export_notes="Export generated successfully",
                    completed_at=generated_at,
                )
                db.add(job)
                generated_count += 1
            except Exception as exc:
                job = ExportJob(
                    scrape_run_id=run_id,
                    export_format=export_format,
                    export_status="failed",
                    file_name=None,
                    file_path=None,
                    file_size_bytes=None,
                    row_count=None,
                    generated_at=generated_at,
                    summary_json={
                        **bundle["summary"],
                        "export_format": export_format,
                    },
                    artifact_metadata_json={
                        "error": str(exc),
                    },
                    export_notes=f"Export generation failed: {exc}",
                    completed_at=None,
                )
                db.add(job)
                failed_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="export_queue_ready",
            items_processed=run.items_processed,
            orchestrator_notes=(
                "Real export artifacts generated "
                f"(success={generated_count}, failed={failed_count})"
            ),
        )

        return run, generated_count

    @staticmethod
    def list_export_jobs(
        db: Session,
        run_id: int | None = None,
        export_status: str | None = None,
    ) -> list[ExportJob]:
        stmt = select(ExportJob).order_by(ExportJob.id.asc())

        if run_id is not None:
            stmt = stmt.where(ExportJob.scrape_run_id == run_id)

        if export_status is not None:
            stmt = stmt.where(ExportJob.export_status == export_status)

        rows = db.scalars(stmt).all()
        return list(rows)

    @staticmethod
    def get_export_job_or_404(db: Session, export_job_id: int) -> ExportJob:
        job = db.get(ExportJob, export_job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export job {export_job_id} not found",
            )
        return job

    @staticmethod
    def mark_completed(
        db: Session,
        export_job_id: int,
        file_name: str | None = None,
        file_path: str | None = None,
        file_size_bytes: int | None = None,
        row_count: int | None = None,
        artifact_metadata_json: dict[str, Any] | None = None,
        export_notes: str | None = None,
    ) -> ExportJob:
        job = ExportService.get_export_job_or_404(db, export_job_id)
        job.export_status = "completed"
        job.file_name = file_name
        job.file_path = file_path
        job.file_size_bytes = file_size_bytes
        job.row_count = row_count
        job.generated_at = job.generated_at or datetime.now(timezone.utc)
        if artifact_metadata_json is not None:
            job.artifact_metadata_json = artifact_metadata_json
        job.export_notes = export_notes or "Export completed"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def mark_failed(
        db: Session,
        export_job_id: int,
        export_notes: str | None = None,
    ) -> ExportJob:
        job = ExportService.get_export_job_or_404(db, export_job_id)
        job.export_status = "failed"
        job.export_notes = export_notes or "Export failed"
        db.commit()
        db.refresh(job)
        return job