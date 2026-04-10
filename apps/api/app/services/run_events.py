from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.run_event import RunEvent


class RunEventService:
    @staticmethod
    def create_event(
        db: Session,
        scrape_run_id: int,
        event_type: str,
        stage: str,
        status: str,
        message: str,
        payload_json: dict | None = None,
    ) -> RunEvent:
        event = RunEvent(
            scrape_run_id=scrape_run_id,
            event_type=event_type,
            stage=stage,
            status=status,
            message=message,
            payload_json=payload_json or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def list_events_for_run(db: Session, scrape_run_id: int) -> list[RunEvent]:
        rows = db.scalars(
            select(RunEvent)
            .where(RunEvent.scrape_run_id == scrape_run_id)
            .order_by(RunEvent.id.asc())
        ).all()
        return list(rows)

    @staticmethod
    def list_recent_events(db: Session, limit: int = 100) -> list[RunEvent]:
        rows = db.scalars(
            select(RunEvent)
            .order_by(RunEvent.id.desc())
            .limit(limit)
        ).all()
        return list(rows)