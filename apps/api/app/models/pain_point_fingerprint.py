"""
Global pain point fingerprint for cross-run deduplication and trend tracking.
Each unique pain point concept gets one row here, referenced by multiple AgentInsights.
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PainPointFingerprint(Base):
    __tablename__ = "pain_point_fingerprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identity
    fingerprint_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    pain_point_label: Mapped[str] = mapped_column(String(255), nullable=False)
    taxonomy_cluster: Mapped[str | None] = mapped_column(String(255), nullable=True)
    competitor_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Trend tracking
    recurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Weekly recurrence counts for trend direction
    count_week_0: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Most recent week
    count_week_1: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_week_2: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_week_3: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Trend direction: rising | stable | declining
    trend_direction: Mapped[str] = mapped_column(String(20), nullable=False, default="stable")

    # Aggregate priority signal
    high_priority_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Example text for display
    example_text: Mapped[str | None] = mapped_column(Text, nullable=True)
