"""add orchestration fields to scrape_runs

Revision ID: 0003_run_orch_fields
Revises: 0002_scrape_runs_raw_ev
Create Date: 2026-04-10 00:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_run_orch_fields"
down_revision: Union[str, None] = "0002_scrape_runs_raw_ev"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scrape_runs",
        sa.Column("pipeline_stage", sa.String(length=50), nullable=False, server_default="created"),
    )
    op.add_column(
        "scrape_runs",
        sa.Column("trigger_mode", sa.String(length=50), nullable=False, server_default="manual"),
    )
    op.add_column(
        "scrape_runs",
        sa.Column("orchestrator_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "scrape_runs",
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scrape_runs_pipeline_stage", "scrape_runs", ["pipeline_stage"])


def downgrade() -> None:
    op.drop_index("ix_scrape_runs_pipeline_stage", table_name="scrape_runs")
    op.drop_column("scrape_runs", "last_heartbeat_at")
    op.drop_column("scrape_runs", "orchestrator_notes")
    op.drop_column("scrape_runs", "trigger_mode")
    op.drop_column("scrape_runs", "pipeline_stage")