"""add notion real sync metadata fields

Revision ID: 0014_notion_real_sync_metadata
Revises: 0013_export_art_meta
Create Date: 2026-04-13 09:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_notion_real_sync_metadata"
down_revision = "0013_export_art_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notion_sync_jobs",
        sa.Column("notion_database_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notion_sync_jobs",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notion_sync_jobs",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "notion_sync_jobs",
        sa.Column("provider_response_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "notion_sync_jobs",
        sa.Column("last_error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "notion_sync_jobs",
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_notion_sync_jobs_notion_database_id",
        "notion_sync_jobs",
        ["notion_database_id"],
        unique=False,
    )
    op.create_index(
        "ix_notion_sync_jobs_idempotency_key",
        "notion_sync_jobs",
        ["idempotency_key"],
        unique=False,
    )

    op.execute(
        "UPDATE notion_sync_jobs SET sync_status = 'queued' WHERE sync_status = 'pending_sync'"
    )
    op.alter_column(
        "notion_sync_jobs",
        "sync_status",
        existing_type=sa.String(length=50),
        server_default="queued",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "notion_sync_jobs",
        "sync_status",
        existing_type=sa.String(length=50),
        server_default="pending_sync",
        existing_nullable=False,
    )
    op.execute(
        "UPDATE notion_sync_jobs SET sync_status = 'pending_sync' WHERE sync_status IN ('queued', 'retrying')"
    )

    op.drop_index("ix_notion_sync_jobs_idempotency_key", table_name="notion_sync_jobs")
    op.drop_index("ix_notion_sync_jobs_notion_database_id", table_name="notion_sync_jobs")

    op.drop_column("notion_sync_jobs", "last_attempted_at")
    op.drop_column("notion_sync_jobs", "last_error_message")
    op.drop_column("notion_sync_jobs", "provider_response_json")
    op.drop_column("notion_sync_jobs", "retry_count")
    op.drop_column("notion_sync_jobs", "idempotency_key")
    op.drop_column("notion_sync_jobs", "notion_database_id")