"""add ingestion metadata fields to raw_evidence

Revision ID: 0012_raw_ev_ing_meta
Revises: 0011_export_jobs_t
Create Date: 2026-04-11 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_raw_ev_ing_meta"
down_revision: str | None = "0011_export_jobs_t"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("raw_evidence", sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("raw_evidence", sa.Column("source_query", sa.String(length=500), nullable=True))
    op.add_column("raw_evidence", sa.Column("parser_version", sa.String(length=50), nullable=True))
    op.add_column("raw_evidence", sa.Column("dedupe_key", sa.String(length=255), nullable=True))
    op.add_column(
        "raw_evidence",
        sa.Column(
            "raw_payload_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )

    op.execute("UPDATE raw_evidence SET raw_payload_json = '{}'::json WHERE raw_payload_json IS NULL")

    op.create_index("ix_raw_evidence_fetched_at", "raw_evidence", ["fetched_at"], unique=False)
    op.create_index("ix_raw_evidence_dedupe_key", "raw_evidence", ["dedupe_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_evidence_dedupe_key", table_name="raw_evidence")
    op.drop_index("ix_raw_evidence_fetched_at", table_name="raw_evidence")

    op.drop_column("raw_evidence", "raw_payload_json")
    op.drop_column("raw_evidence", "dedupe_key")
    op.drop_column("raw_evidence", "parser_version")
    op.drop_column("raw_evidence", "source_query")
    op.drop_column("raw_evidence", "fetched_at")