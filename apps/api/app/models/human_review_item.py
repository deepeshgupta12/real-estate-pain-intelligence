from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HumanReviewItem(Base):
    __tablename__ = "human_review_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id: Mapped[int] = mapped_column(
        ForeignKey("scrape_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_insight_id: Mapped[int] = mapped_column(
        ForeignKey("agent_insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_review",
        server_default="pending_review",
        index=True,
    )
    reviewer_decision: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority_label: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )