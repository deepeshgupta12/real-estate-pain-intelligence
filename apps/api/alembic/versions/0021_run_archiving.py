"""Add archived_at column to scrape_runs for data retention

Revision ID: 0021_run_archiving
Revises: 0020_session_notes_multi_source
Create Date: 2026-04-15

Adds:
  - scrape_runs.archived_at (TIMESTAMPTZ, nullable) — set when a run is archived
  - index on archived_at for efficient filtering of active vs archived runs
"""
from alembic import op
import sqlalchemy as sa

revision = "0021_run_archiving"
down_revision = "0020_session_notes_multi_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scrape_runs",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scrape_runs_archived_at", "scrape_runs", ["archived_at"])


def downgrade() -> None:
    op.drop_index("ix_scrape_runs_archived_at", table_name="scrape_runs")
    op.drop_column("scrape_runs", "archived_at")
