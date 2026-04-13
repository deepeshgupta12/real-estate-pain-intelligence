"""Add pain_point_fingerprints table for cross-run trending

Revision ID: 0018_pain_point_fingerprints
Revises: 0017_system_state_cascade
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0018_pain_point_fingerprints"
down_revision = "0017_system_state_cascade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pain_point_fingerprints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fingerprint_key", sa.String(64), nullable=False),
        sa.Column("pain_point_label", sa.String(255), nullable=False),
        sa.Column("taxonomy_cluster", sa.String(255), nullable=True),
        sa.Column("competitor_label", sa.String(255), nullable=True),
        sa.Column("recurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("count_week_0", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("count_week_1", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("count_week_2", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("count_week_3", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trend_direction", sa.String(20), nullable=False, server_default="stable"),
        sa.Column("high_priority_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_priority_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("example_text", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ppf_fingerprint_key", "pain_point_fingerprints", ["fingerprint_key"], unique=True)
    op.create_index("ix_ppf_taxonomy", "pain_point_fingerprints", ["taxonomy_cluster"])
    op.create_index("ix_ppf_recurrence", "pain_point_fingerprints", ["recurrence_count"])


def downgrade() -> None:
    op.drop_index("ix_ppf_recurrence", table_name="pain_point_fingerprints")
    op.drop_index("ix_ppf_taxonomy", table_name="pain_point_fingerprints")
    op.drop_index("ix_ppf_fingerprint_key", table_name="pain_point_fingerprints")
    op.drop_table("pain_point_fingerprints")
