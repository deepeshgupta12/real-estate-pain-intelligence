from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.export_job import ExportJob
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService


class ExportService:
    SUPPORTED_FORMATS = {"csv", "json", "pdf"}

    @staticmethod
    def generate_export_jobs(db: Session, run_id: int, export_formats: list[str]) -> tuple[ScrapeRun, int]:
        run = OrchestratorService.get_run_or_404(db, run_id)

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

        evidence_count = db.scalar(
            select(func.count(RawEvidence.id)).where(RawEvidence.scrape_run_id == run_id)
        )
        insight_count = db.scalar(
            select(func.count(AgentInsight.id)).where(AgentInsight.scrape_run_id == run_id)
        )

        db.execute(delete(ExportJob).where(ExportJob.scrape_run_id == run_id))
        db.commit()

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="export_generation",
            orchestrator_notes="Export job generation started",
        )

        generated_count = 0

        for export_format in cleaned_formats:
            job = ExportJob(
                scrape_run_id=run_id,
                export_format=export_format,
                export_status="pending",
                file_name=None,
                file_path=None,
                summary_json={
                    "evidence_count": evidence_count or 0,
                    "insight_count": insight_count or 0,
                    "export_format": export_format,
                },
                export_notes=f"{export_format.upper()} export prepared",
            )
            db.add(job)
            generated_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="export_queue_ready",
            items_processed=run.items_processed,
            orchestrator_notes="Export jobs generated successfully",
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
        export_notes: str | None = None,
    ) -> ExportJob:
        job = ExportService.get_export_job_or_404(db, export_job_id)
        job.export_status = "completed"
        job.file_name = file_name
        job.file_path = file_path
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