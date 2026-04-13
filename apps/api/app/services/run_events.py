from collections import OrderedDict
from datetime import datetime
from typing import Any

from sqlalchemy import Select, desc, select
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
        payload_json: dict[str, Any] | None = None,
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
    def _apply_filters(
        stmt: Select,
        scrape_run_id: int | None = None,
        event_type: str | None = None,
        stage: str | None = None,
        status: str | None = None,
    ) -> Select:
        if scrape_run_id is not None:
            stmt = stmt.where(RunEvent.scrape_run_id == scrape_run_id)
        if event_type is not None:
            stmt = stmt.where(RunEvent.event_type == event_type)
        if stage is not None:
            stmt = stmt.where(RunEvent.stage == stage)
        if status is not None:
            stmt = stmt.where(RunEvent.status == status)
        return stmt

    @staticmethod
    def list_events(
        db: Session,
        scrape_run_id: int | None = None,
        event_type: str | None = None,
        stage: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
        newest_first: bool = True,
    ) -> list[RunEvent]:
        stmt = select(RunEvent)
        stmt = RunEventService._apply_filters(
            stmt=stmt,
            scrape_run_id=scrape_run_id,
            event_type=event_type,
            stage=stage,
            status=status,
        )
        stmt = stmt.order_by(desc(RunEvent.id) if newest_first else RunEvent.id.asc())
        stmt = stmt.offset(offset).limit(limit)
        rows = db.scalars(stmt).all()
        return list(rows)

    @staticmethod
    def list_events_for_run(
        db: Session,
        scrape_run_id: int,
        event_type: str | None = None,
        stage: str | None = None,
        status: str | None = None,
        limit: int = 200,
        offset: int = 0,
        newest_first: bool = False,
    ) -> list[RunEvent]:
        return RunEventService.list_events(
            db=db,
            scrape_run_id=scrape_run_id,
            event_type=event_type,
            stage=stage,
            status=status,
            limit=limit,
            offset=offset,
            newest_first=newest_first,
        )

    @staticmethod
    def list_recent_events(
        db: Session,
        limit: int = 100,
    ) -> list[RunEvent]:
        return RunEventService.list_events(
            db=db,
            scrape_run_id=None,
            limit=limit,
            newest_first=True,
        )

    @staticmethod
    def get_latest_event_for_run(db: Session, scrape_run_id: int) -> RunEvent | None:
        stmt = (
            select(RunEvent)
            .where(RunEvent.scrape_run_id == scrape_run_id)
            .order_by(desc(RunEvent.id))
            .limit(1)
        )
        return db.scalars(stmt).first()

    @staticmethod
    def build_stage_timeline(db: Session, scrape_run_id: int) -> list[dict[str, Any]]:
        events = RunEventService.list_events_for_run(
            db=db,
            scrape_run_id=scrape_run_id,
            newest_first=False,
            limit=1000,
        )

        stage_map: "OrderedDict[str, dict[str, Any]]" = OrderedDict()

        for event in events:
            if event.stage not in stage_map:
                stage_map[event.stage] = {
                    "stage": event.stage,
                    "first_event_at": event.created_at,
                    "last_event_at": event.created_at,
                    "latest_status": event.status,
                    "event_count": 1,
                }
                continue

            stage_map[event.stage]["last_event_at"] = event.created_at
            stage_map[event.stage]["latest_status"] = event.status
            stage_map[event.stage]["event_count"] += 1

        timeline: list[dict[str, Any]] = []
        for item in stage_map.values():
            first_event_at = item["first_event_at"]
            last_event_at = item["last_event_at"]
            duration_seconds = int((last_event_at - first_event_at).total_seconds())
            timeline.append(
                {
                    "stage": item["stage"],
                    "first_event_at": first_event_at,
                    "last_event_at": last_event_at,
                    "latest_status": item["latest_status"],
                    "event_count": item["event_count"],
                    "duration_seconds": max(duration_seconds, 0),
                }
            )

        return timeline

    @staticmethod
    def count_events_since(
        db: Session,
        since: datetime,
        scrape_run_id: int | None = None,
    ) -> int:
        stmt = select(RunEvent).where(RunEvent.created_at >= since)
        if scrape_run_id is not None:
            stmt = stmt.where(RunEvent.scrape_run_id == scrape_run_id)
        rows = db.scalars(stmt).all()
        return len(list(rows))