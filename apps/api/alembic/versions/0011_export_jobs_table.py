"""create export_jobs table

Revision ID: 0011_export_jobs_t
Revises: 0010_notion_sync_j
Create Date: 2026-04-10 03:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_export_jobs_t"
down_revision: Union[str, None] = "0010_notion_sync_j"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("export_format", sa.String(length=20), nullable=False),
        sa.Column("export_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("export_notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scrape_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_export_jobs_scrape_run_id", "export_jobs", ["scrape_run_id"])
    op.create_index("ix_export_jobs_export_format", "export_jobs", ["export_format"])
    op.create_index("ix_export_jobs_export_status", "export_jobs", ["export_status"])


def downgrade() -> None:
    op.drop_index("ix_export_jobs_export_status", table_name="export_jobs")
    op.drop_index("ix_export_jobs_export_format", table_name="export_jobs")
    op.drop_index("ix_export_jobs_scrape_run_id", table_name="export_jobs")
    op.drop_table("export_jobs")