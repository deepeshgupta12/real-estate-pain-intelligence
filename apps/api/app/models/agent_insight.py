from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentInsight(Base):
    __tablename__ = "agent_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id: Mapped[int] = mapped_column(
        ForeignKey("scrape_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_evidence_id: Mapped[int] = mapped_column(
        ForeignKey("raw_evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    journey_stage: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    pain_point_label: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    pain_point_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    taxonomy_cluster: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    root_cause_hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_label: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    priority_label: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    action_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[str | None] = mapped_column(String(20), nullable=True)
    insight_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="generated",
        server_default="generated",
        index=True,
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )