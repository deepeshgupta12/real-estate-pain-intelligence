"""create scrape_runs and raw_evidence tables

Revision ID: 0002_scrape_runs_raw_ev
Revises: 0001_create_system_state
Create Date: 2026-04-10 00:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_scrape_runs_raw_ev"
down_revision: Union[str, None] = "0001_create_system_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("target_brand", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("items_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scrape_runs_source_name", "scrape_runs", ["source_name"])
    op.create_index("ix_scrape_runs_target_brand", "scrape_runs", ["target_brand"])

    op.create_table(
        "raw_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("platform_name", sa.String(length=100), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("is_relevant", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scrape_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_evidence_scrape_run_id", "raw_evidence", ["scrape_run_id"])
    op.create_index("ix_raw_evidence_source_name", "raw_evidence", ["source_name"])
    op.create_index("ix_raw_evidence_platform_name", "raw_evidence", ["platform_name"])
    op.create_index("ix_raw_evidence_external_id", "raw_evidence", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_raw_evidence_external_id", table_name="raw_evidence")
    op.drop_index("ix_raw_evidence_platform_name", table_name="raw_evidence")
    op.drop_index("ix_raw_evidence_source_name", table_name="raw_evidence")
    op.drop_index("ix_raw_evidence_scrape_run_id", table_name="raw_evidence")
    op.drop_table("raw_evidence")

    op.drop_index("ix_scrape_runs_target_brand", table_name="scrape_runs")
    op.drop_index("ix_scrape_runs_source_name", table_name="scrape_runs")
    op.drop_table("scrape_runs")