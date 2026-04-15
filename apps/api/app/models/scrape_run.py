from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.raw_evidence import RawEvidence


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Organization scoping — nullable for backward compat with pre-multi-tenant runs.
    # Added to DB in migration 0019; ORM field added in Step 37.
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Comma-separated list of source names, e.g. "reddit" or "reddit,youtube,app_reviews".
    # Widened to Text (migration 0020) so all 5 sources fit without truncation.
    source_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    target_brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created")
    pipeline_stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="created",
        server_default="created",
        index=True,
    )
    trigger_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        server_default="manual",
    )
    items_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    orchestrator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # User-authored context entered at run-creation time.
    # Separate from orchestrator_notes which is overwritten by the pipeline.
    session_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Data retention — set when operator archives a run; archived runs are hidden from
    # the active queue and default listings unless explicitly requested.
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    evidence_items: Mapped[list["RawEvidence"]] = relationship(
        back_populates="scrape_run",
        cascade="all, delete-orphan",
    )