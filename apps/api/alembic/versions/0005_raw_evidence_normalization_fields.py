"""add normalization fields to raw_evidence

Revision ID: 0005_raw_ev_norm
Revises: 0004_run_events_tbl
Create Date: 2026-04-10 00:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_raw_ev_norm"
down_revision: Union[str, None] = "0004_run_events_tbl"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "raw_evidence",
        sa.Column("normalized_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("normalized_language", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("normalization_status", sa.String(length=50), nullable=False, server_default="pending"),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("normalization_hash", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_raw_evidence_normalization_status", "raw_evidence", ["normalization_status"])
    op.create_index("ix_raw_evidence_normalization_hash", "raw_evidence", ["normalization_hash"])


def downgrade() -> None:
    op.drop_index("ix_raw_evidence_normalization_hash", table_name="raw_evidence")
    op.drop_index("ix_raw_evidence_normalization_status", table_name="raw_evidence")
    op.drop_column("raw_evidence", "normalization_hash")
    op.drop_column("raw_evidence", "normalization_status")
    op.drop_column("raw_evidence", "normalized_language")
    op.drop_column("raw_evidence", "normalized_text")