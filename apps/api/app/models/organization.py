"""Organization model for multi-tenancy."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")  # free | pro | enterprise
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_runs_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    api_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob for org settings
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    owner_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
