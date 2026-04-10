"""create agent_insights table

Revision ID: 0007_agent_insights
Revises: 0006_raw_ev_multi
Create Date: 2026-04-10 01:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_agent_insights"
down_revision: Union[str, None] = "0006_raw_ev_multi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("raw_evidence_id", sa.Integer(), nullable=False),
        sa.Column("journey_stage", sa.String(length=100), nullable=True),
        sa.Column("pain_point_label", sa.String(length=255), nullable=True),
        sa.Column("pain_point_summary", sa.Text(), nullable=True),
        sa.Column("taxonomy_cluster", sa.String(length=100), nullable=True),
        sa.Column("root_cause_hypothesis", sa.Text(), nullable=True),
        sa.Column("competitor_label", sa.String(length=100), nullable=True),
        sa.Column("priority_label", sa.String(length=50), nullable=True),
        sa.Column("action_recommendation", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.String(length=20), nullable=True),
        sa.Column("insight_status", sa.String(length=50), nullable=False, server_default="generated"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scrape_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_evidence_id"], ["raw_evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_insights_scrape_run_id", "agent_insights", ["scrape_run_id"])
    op.create_index("ix_agent_insights_raw_evidence_id", "agent_insights", ["raw_evidence_id"])
    op.create_index("ix_agent_insights_journey_stage", "agent_insights", ["journey_stage"])
    op.create_index("ix_agent_insights_pain_point_label", "agent_insights", ["pain_point_label"])
    op.create_index("ix_agent_insights_taxonomy_cluster", "agent_insights", ["taxonomy_cluster"])
    op.create_index("ix_agent_insights_competitor_label", "agent_insights", ["competitor_label"])
    op.create_index("ix_agent_insights_priority_label", "agent_insights", ["priority_label"])
    op.create_index("ix_agent_insights_insight_status", "agent_insights", ["insight_status"])


def downgrade() -> None:
    op.drop_index("ix_agent_insights_insight_status", table_name="agent_insights")
    op.drop_index("ix_agent_insights_priority_label", table_name="agent_insights")
    op.drop_index("ix_agent_insights_competitor_label", table_name="agent_insights")
    op.drop_index("ix_agent_insights_taxonomy_cluster", table_name="agent_insights")
    op.drop_index("ix_agent_insights_pain_point_label", table_name="agent_insights")
    op.drop_index("ix_agent_insights_journey_stage", table_name="agent_insights")
    op.drop_index("ix_agent_insights_raw_evidence_id", table_name="agent_insights")
    op.drop_index("ix_agent_insights_scrape_run_id", table_name="agent_insights")
    op.drop_table("agent_insights")