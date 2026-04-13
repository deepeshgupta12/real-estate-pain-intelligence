from datetime import datetime

from pgvector.sqlalchemy import Vector
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

    embedding_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    embedding_model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Legacy JSON copy kept for compatibility / export readability
    embedding_vector_json: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    # Native pgvector column
    embedding_vector: Mapped[list[float] | None] = mapped_column(Vector(64), nullable=True)

    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )