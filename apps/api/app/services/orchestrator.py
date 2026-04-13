from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.run_event import RunEvent
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
    def _heartbeat_age_seconds(last_heartbeat_at: datetime | None) -> int | None:
        if last_heartbeat_at is None:
            return None
        now = datetime.now(timezone.utc)
        age_seconds = int((now - last_heartbeat_at).total_seconds())
        return max(age_seconds, 0)

    @staticmethod
    def _is_stale(run: ScrapeRun) -> bool:
        if run.status not in {"queued", "running"}:
            return False

        heartbeat_age_seconds = OrchestratorService._heartbeat_age_seconds(run.last_heartbeat_at)
        if heartbeat_age_seconds is None:
            return False

        settings = get_settings()
        return heartbeat_age_seconds > settings.observability_stale_run_seconds

    @staticmethod
    def _health_label(run: ScrapeRun, is_stale: bool) -> str:
        if run.status == "failed":
            return "failed"
        if run.status == "completed":
            return "completed"
        if is_stale:
            return "stale"
        if run.status == "queued":
            return "waiting"
        if run.status == "running":
            return "healthy"
        return run.status

    @staticmethod
    def _build_latest_event_snapshot(event: RunEvent | None) -> dict[str, Any] | None:
        if event is None:
            return None

        return {
            "id": event.id,
            "event_type": event.event_type,
            "stage": event.stage,
            "status": event.status,
            "message": event.message,
            "created_at": event.created_at,
        }

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

    @staticmethod
    def list_active_queue_summaries(db: Session) -> list[dict[str, Any]]:
        runs = OrchestratorService.list_active_queue(db)
        summaries: list[dict[str, Any]] = []

        for run in runs:
            latest_event = RunEventService.get_latest_event_for_run(db, scrape_run_id=run.id)
            heartbeat_age_seconds = OrchestratorService._heartbeat_age_seconds(run.last_heartbeat_at)
            is_stale = OrchestratorService._is_stale(run)

            summaries.append(
                {
                    "run_id": run.id,
                    "source_name": run.source_name,
                    "target_brand": run.target_brand,
                    "status": run.status,
                    "pipeline_stage": run.pipeline_stage,
                    "items_discovered": run.items_discovered,
                    "items_processed": run.items_processed,
                    "last_heartbeat_at": run.last_heartbeat_at,
                    "orchestrator_notes": run.orchestrator_notes,
                    "heartbeat_age_seconds": heartbeat_age_seconds,
                    "is_stale": is_stale,
                    "health_label": OrchestratorService._health_label(run, is_stale=is_stale),
                    "latest_event_type": latest_event.event_type if latest_event else None,
                    "latest_event_at": latest_event.created_at if latest_event else None,
                    "latest_event_message": latest_event.message if latest_event else None,
                }
            )

        return summaries

    @staticmethod
    def build_run_diagnostics(db: Session, run_id: int) -> dict[str, Any]:
        from app.services.final_hardening import FinalHardeningService

        run = OrchestratorService.get_run_or_404(db, run_id)

        events = RunEventService.list_events_for_run(
            db=db,
            scrape_run_id=run_id,
            newest_first=False,
            limit=1000,
        )
        latest_event = events[-1] if events else None
        stage_timeline = RunEventService.build_stage_timeline(db=db, scrape_run_id=run_id)
        readiness = FinalHardeningService.build_run_readiness(db=db, run_id=run_id)

        heartbeat_age_seconds = OrchestratorService._heartbeat_age_seconds(run.last_heartbeat_at)
        is_stale = OrchestratorService._is_stale(run)
        health_label = OrchestratorService._health_label(run, is_stale=is_stale)

        fail_event = None
        last_successful_stage = None
        for event in events:
            if event.status != "failed" and event.stage != "failed":
                last_successful_stage = event.stage
            if event.event_type == "fail" or event.status == "failed":
                fail_event = event

        failure_snapshot = {
            "failed": run.status == "failed",
            "error_message": run.error_message,
            "failed_at": fail_event.created_at if fail_event else None,
            "failed_stage": fail_event.stage if fail_event else ("failed" if run.status == "failed" else None),
            "failed_event_message": fail_event.message if fail_event else None,
            "last_successful_stage": last_successful_stage,
        }

        return {
            "run_id": run.id,
            "source_name": run.source_name,
            "target_brand": run.target_brand,
            "status": run.status,
            "pipeline_stage": run.pipeline_stage,
            "trigger_mode": run.trigger_mode,
            "items_discovered": run.items_discovered,
            "items_processed": run.items_processed,
            "started_at": run.started_at,
            "last_heartbeat_at": run.last_heartbeat_at,
            "completed_at": run.completed_at,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "error_message": run.error_message,
            "orchestrator_notes": run.orchestrator_notes,
            "heartbeat_age_seconds": heartbeat_age_seconds,
            "is_stale": is_stale,
            "health_label": health_label,
            "total_events": len(events),
            "latest_event": OrchestratorService._build_latest_event_snapshot(latest_event),
            "stage_timeline": stage_timeline,
            "readiness_checks": dict(readiness["checks"]),
            "readiness_counts": {
                key: int(value) for key, value in dict(readiness["counts"]).items() if isinstance(value, int)
            },
            "failure_snapshot": failure_snapshot,
            "metadata": {
                "stale_threshold_seconds": get_settings().observability_stale_run_seconds,
            },
        }