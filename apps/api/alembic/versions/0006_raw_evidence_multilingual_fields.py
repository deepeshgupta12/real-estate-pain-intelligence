"""add multilingual fields to raw_evidence

Revision ID: 0006_raw_ev_multi
Revises: 0005_raw_ev_norm
Create Date: 2026-04-10 01:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_raw_ev_multi"
down_revision: Union[str, None] = "0005_raw_ev_norm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "raw_evidence",
        sa.Column("resolved_language", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("language_family", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("script_label", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("multilingual_status", sa.String(length=50), nullable=False, server_default="pending"),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("multilingual_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "raw_evidence",
        sa.Column("bridge_text", sa.Text(), nullable=True),
    )
    op.create_index("ix_raw_evidence_resolved_language", "raw_evidence", ["resolved_language"])
    op.create_index("ix_raw_evidence_multilingual_status", "raw_evidence", ["multilingual_status"])


def downgrade() -> None:
    op.drop_index("ix_raw_evidence_multilingual_status", table_name="raw_evidence")
    op.drop_index("ix_raw_evidence_resolved_language", table_name="raw_evidence")
    op.drop_column("raw_evidence", "bridge_text")
    op.drop_column("raw_evidence", "multilingual_notes")
    op.drop_column("raw_evidence", "multilingual_status")
    op.drop_column("raw_evidence", "script_label")
    op.drop_column("raw_evidence", "language_family")
    op.drop_column("raw_evidence", "resolved_language")