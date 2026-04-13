"""Add organizations table for multi-tenancy

Revision ID: 0019_organizations
Revises: 0018_pain_point_fingerprints
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0019_organizations"
down_revision = "0018_pain_point_fingerprints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_runs_per_month", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("api_key", sa.String(64), nullable=True),
        sa.Column("settings_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("owner_email", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_api_key", "organizations", ["api_key"], unique=True)

    # Add organization_id to scrape_runs for scoping (nullable for backward compat)
    op.add_column("scrape_runs", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_index("ix_scrape_runs_org_id", "scrape_runs", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_scrape_runs_org_id", table_name="scrape_runs")
    op.drop_column("scrape_runs", "organization_id")
    op.drop_index("ix_organizations_api_key", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
