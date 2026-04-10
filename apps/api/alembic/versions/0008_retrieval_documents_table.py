"""create retrieval_documents table

Revision ID: 0008_retrieval_docs
Revises: 0007_agent_insights
Create Date: 2026-04-10 01:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_retrieval_docs"
down_revision: Union[str, None] = "0007_agent_insights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retrieval_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("raw_evidence_id", sa.Integer(), nullable=False),
        sa.Column("agent_insight_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("document_text", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("language_code", sa.String(length=50), nullable=True),
        sa.Column("retrieval_status", sa.String(length=50), nullable=False, server_default="indexed"),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scrape_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_evidence_id"], ["raw_evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_insight_id"], ["agent_insights.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retrieval_documents_scrape_run_id", "retrieval_documents", ["scrape_run_id"])
    op.create_index("ix_retrieval_documents_raw_evidence_id", "retrieval_documents", ["raw_evidence_id"])
    op.create_index("ix_retrieval_documents_agent_insight_id", "retrieval_documents", ["agent_insight_id"])
    op.create_index("ix_retrieval_documents_document_type", "retrieval_documents", ["document_type"])
    op.create_index("ix_retrieval_documents_language_code", "retrieval_documents", ["language_code"])
    op.create_index("ix_retrieval_documents_retrieval_status", "retrieval_documents", ["retrieval_status"])


def downgrade() -> None:
    op.drop_index("ix_retrieval_documents_retrieval_status", table_name="retrieval_documents")
    op.drop_index("ix_retrieval_documents_language_code", table_name="retrieval_documents")
    op.drop_index("ix_retrieval_documents_document_type", table_name="retrieval_documents")
    op.drop_index("ix_retrieval_documents_agent_insight_id", table_name="retrieval_documents")
    op.drop_index("ix_retrieval_documents_raw_evidence_id", table_name="retrieval_documents")
    op.drop_index("ix_retrieval_documents_scrape_run_id", table_name="retrieval_documents")
    op.drop_table("retrieval_documents")