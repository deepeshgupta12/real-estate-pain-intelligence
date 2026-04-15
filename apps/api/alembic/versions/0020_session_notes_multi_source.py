"""Add session_notes and widen source_name on scrape_runs for multi-platform support

Revision ID: 0020_session_notes_multi_source
Revises: 0019_organizations
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0020_session_notes_multi_source"
down_revision = "0019_organizations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # session_notes: user-authored context entered at run-creation time.
    # Kept separate from orchestrator_notes which is overwritten by the pipeline.
    op.add_column(
        "scrape_runs",
        sa.Column("session_notes", sa.Text(), nullable=True),
    )

    # Widen source_name from String(100) to Text so comma-separated multi-source
    # values like "reddit,youtube,app_reviews" are stored without length risk.
    op.alter_column(
        "scrape_runs",
        "source_name",
        existing_type=sa.String(100),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "scrape_runs",
        "source_name",
        existing_type=sa.Text(),
        type_=sa.String(100),
        existing_nullable=False,
    )
    op.drop_column("scrape_runs", "session_notes")
