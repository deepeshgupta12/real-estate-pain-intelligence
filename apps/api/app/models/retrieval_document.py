from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RetrievalDocument(Base):
    __tablename__ = "retrieval_documents"

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
    agent_insight_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_insights.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_text: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    language_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    retrieval_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="indexed",
        server_default="indexed",
        index=True,
    )
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )