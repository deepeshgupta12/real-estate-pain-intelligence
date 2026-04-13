from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotionSyncJob(Base):
    __tablename__ = "notion_sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id: Mapped[int] = mapped_column(
        ForeignKey("scrape_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    human_review_item_id: Mapped[int] = mapped_column(
        ForeignKey("human_review_queue.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sync_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        server_default="queued",
        index=True,
    )
    destination_label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="notion_database",
        server_default="notion_database",
    )
    notion_page_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    notion_database_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    sync_payload_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    provider_response_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    sync_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )