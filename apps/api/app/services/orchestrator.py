from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scrape_run import ScrapeRun
from app.services.run_events import RunEventService


class OrchestratorService:
    @staticmethod
    def get_run_or_404(db: Session, run_id: int) -> ScrapeRun:
        run = db.get(ScrapeRun, run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scrape run {run_id} not found",
            )
        return run

    @staticmethod
    def dispatch_run(db: Session, run_id: int) -> ScrapeRun:
        run = OrchestratorService.get_run_or_404(db, run_id)
        now = datetime.now(timezone.utc)

        run.status = "queued"
        run.pipeline_stage = "dispatched"
        run.trigger_mode = run.trigger_mode or "manual"
        run.last_heartbeat_at = now
        run.orchestrator_notes = "Run dispatched to orchestrator queue"

        db.commit()
        db.refresh(run)

        RunEventService.create_event(
            db=db,
            scrape_run_id=run.id,
            event_type="dispatch",
            stage=run.pipeline_stage,
            status=run.status,
            message="Run dispatched to orchestrator queue",
            payload_json={"trigger_mode": run.trigger_mode},
        )
        return run

    @staticmethod
    def start_run(db: Session, run_id: int) -> ScrapeRun:
        run = OrchestratorService.get_run_or_404(db, run_id)
        now = datetime.now(timezone.utc)

        run.status = "running"
        run.pipeline_stage = "ingestion"
        run.started_at = run.started_at or now
        run.last_heartbeat_at = now
        run.orchestrator_notes = "Run picked by orchestrator and started"

        db.commit()
        db.refresh(run)

        RunEventService.create_event(
            db=db,
            scrape_run_id=run.id,
            event_type="start",
            stage=run.pipeline_stage,
            status=run.status,
            message="Run picked by orchestrator and started",
            payload_json={"started_at": run.started_at.isoformat() if run.started_at else None},
        )
        return run

    @staticmethod
    def update_progress(
        db: Session,
        run_id: int,
        pipeline_stage: str,
        items_discovered: int | None = None,
        items_processed: int | None = None,
        orchestrator_notes: str | None = None,
    ) -> ScrapeRun:
        run = OrchestratorService.get_run_or_404(db, run_id)
        now = datetime.now(timezone.utc)

        run.status = "running"
        run.pipeline_stage = pipeline_stage
        run.last_heartbeat_at = now

        if items_discovered is not None:
            run.items_discovered = items_discovered
        if items_processed is not None:
            run.items_processed = items_processed
        if orchestrator_notes is not None:
            run.orchestrator_notes = orchestrator_notes

        db.commit()
        db.refresh(run)

        RunEventService.create_event(
            db=db,
            scrape_run_id=run.id,
            event_type="progress",
            stage=run.pipeline_stage,
            status=run.status,
            message=run.orchestrator_notes or "Run progress updated",
            payload_json={
                "items_discovered": run.items_discovered,
                "items_processed": run.items_processed,
            },
        )
        return run

    @staticmethod
    def complete_run(db: Session, run_id: int) -> ScrapeRun:
        run = OrchestratorService.get_run_or_404(db, run_id)
        now = datetime.now(timezone.utc)

        run.status = "completed"
        run.pipeline_stage = "completed"
        run.last_heartbeat_at = now
        run.completed_at = now
        run.orchestrator_notes = "Run completed successfully"

        db.commit()
        db.refresh(run)

        RunEventService.create_event(
            db=db,
            scrape_run_id=run.id,
            event_type="complete",
            stage=run.pipeline_stage,
            status=run.status,
            message="Run completed successfully",
            payload_json={"completed_at": run.completed_at.isoformat() if run.completed_at else None},
        )
        return run

    @staticmethod
    def fail_run(
        db: Session,
        run_id: int,
        error_message: str,
        orchestrator_notes: str | None = None,
    ) -> ScrapeRun:
        run = OrchestratorService.get_run_or_404(db, run_id)
        now = datetime.now(timezone.utc)

        run.status = "failed"
        run.pipeline_stage = "failed"
        run.error_message = error_message
        run.last_heartbeat_at = now
        run.orchestrator_notes = orchestrator_notes or "Run failed during orchestration"

        db.commit()
        db.refresh(run)

        RunEventService.create_event(
            db=db,
            scrape_run_id=run.id,
            event_type="fail",
            stage=run.pipeline_stage,
            status=run.status,
            message=run.orchestrator_notes,
            payload_json={"error_message": error_message},
        )
        return run

    @staticmethod
    def list_active_queue(db: Session) -> list[ScrapeRun]:
        rows = db.scalars(
            select(ScrapeRun)
            .where(ScrapeRun.status.in_(["queued", "running"]))
            .order_by(ScrapeRun.id.desc())
        ).all()
        return list(rows)