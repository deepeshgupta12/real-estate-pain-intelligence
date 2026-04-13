"""add retrieval embedding fields without pgvector

Revision ID: 0015_retrieval_embed
Revises: 0014_notion_real_sync_metadata
Create Date: 2026-04-13 10:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_retrieval_embed"
down_revision = "0014_notion_real_sync_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "retrieval_documents",
        sa.Column(
            "embedding_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "retrieval_documents",
        sa.Column("embedding_model_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "retrieval_documents",
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
    )
    op.add_column(
        "retrieval_documents",
        sa.Column("embedding_vector_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "retrieval_documents",
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_retrieval_documents_embedding_status",
        "retrieval_documents",
        ["embedding_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_retrieval_documents_embedding_status", table_name="retrieval_documents")
    op.drop_column("retrieval_documents", "embedded_at")
    op.drop_column("retrieval_documents", "embedding_vector_json")
    op.drop_column("retrieval_documents", "embedding_dimensions")
    op.drop_column("retrieval_documents", "embedding_model_name")
    op.drop_column("retrieval_documents", "embedding_status")