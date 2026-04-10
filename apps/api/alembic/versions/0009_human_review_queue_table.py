"""create human_review_queue table

Revision ID: 0009_human_review_q
Revises: 0008_retrieval_docs
Create Date: 2026-04-10 02:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_human_review_q"
down_revision: Union[str, None] = "0008_retrieval_docs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "human_review_queue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("agent_insight_id", sa.Integer(), nullable=False),
        sa.Column("review_status", sa.String(length=50), nullable=False, server_default="pending_review"),
        sa.Column("reviewer_decision", sa.String(length=50), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("source_summary", sa.Text(), nullable=True),
        sa.Column("priority_label", sa.String(length=50), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scrape_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_insight_id"], ["agent_insights.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_human_review_queue_scrape_run_id", "human_review_queue", ["scrape_run_id"])
    op.create_index("ix_human_review_queue_agent_insight_id", "human_review_queue", ["agent_insight_id"])
    op.create_index("ix_human_review_queue_review_status", "human_review_queue", ["review_status"])
    op.create_index("ix_human_review_queue_reviewer_decision", "human_review_queue", ["reviewer_decision"])
    op.create_index("ix_human_review_queue_priority_label", "human_review_queue", ["priority_label"])


def downgrade() -> None:
    op.drop_index("ix_human_review_queue_priority_label", table_name="human_review_queue")
    op.drop_index("ix_human_review_queue_reviewer_decision", table_name="human_review_queue")
    op.drop_index("ix_human_review_queue_review_status", table_name="human_review_queue")
    op.drop_index("ix_human_review_queue_agent_insight_id", table_name="human_review_queue")
    op.drop_index("ix_human_review_queue_scrape_run_id", table_name="human_review_queue")
    op.drop_table("human_review_queue")