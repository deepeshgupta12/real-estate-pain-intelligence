"""create notion_sync_jobs table

Revision ID: 0010_notion_sync_j
Revises: 0009_human_review_q
Create Date: 2026-04-10 03:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_notion_sync_j"
down_revision: Union[str, None] = "0009_human_review_q"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notion_sync_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("human_review_item_id", sa.Integer(), nullable=False),
        sa.Column("sync_status", sa.String(length=50), nullable=False, server_default="pending_sync"),
        sa.Column("destination_label", sa.String(length=100), nullable=False, server_default="notion_database"),
        sa.Column("notion_page_id", sa.String(length=255), nullable=True),
        sa.Column("sync_payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("sync_notes", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scrape_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["human_review_item_id"], ["human_review_queue.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notion_sync_jobs_scrape_run_id", "notion_sync_jobs", ["scrape_run_id"])
    op.create_index("ix_notion_sync_jobs_human_review_item_id", "notion_sync_jobs", ["human_review_item_id"])
    op.create_index("ix_notion_sync_jobs_sync_status", "notion_sync_jobs", ["sync_status"])
    op.create_index("ix_notion_sync_jobs_notion_page_id", "notion_sync_jobs", ["notion_page_id"])


def downgrade() -> None:
    op.drop_index("ix_notion_sync_jobs_notion_page_id", table_name="notion_sync_jobs")
    op.drop_index("ix_notion_sync_jobs_sync_status", table_name="notion_sync_jobs")
    op.drop_index("ix_notion_sync_jobs_human_review_item_id", table_name="notion_sync_jobs")
    op.drop_index("ix_notion_sync_jobs_scrape_run_id", table_name="notion_sync_jobs")
    op.drop_table("notion_sync_jobs")