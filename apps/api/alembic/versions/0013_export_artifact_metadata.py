"""add export artifact metadata fields

Revision ID: 0013_export_art_meta
Revises: 0012_raw_ev_ing_meta
Create Date: 2026-04-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_export_art_meta"
down_revision = "0012_raw_ev_ing_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("export_jobs", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("export_jobs", sa.Column("row_count", sa.Integer(), nullable=True))
    op.add_column("export_jobs", sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "export_jobs",
        sa.Column(
            "artifact_metadata_json",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("export_jobs", "artifact_metadata_json")
    op.drop_column("export_jobs", "generated_at")
    op.drop_column("export_jobs", "row_count")
    op.drop_column("export_jobs", "file_size_bytes")