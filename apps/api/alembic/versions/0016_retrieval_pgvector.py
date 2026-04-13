"""upgrade retrieval embeddings to native pgvector

Revision ID: 0016_retrieval_pgvector
Revises: 0015_retrieval_embed
Create Date: 2026-04-13 11:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0016_retrieval_pgvector"
down_revision = "0015_retrieval_embed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "retrieval_documents",
        sa.Column("embedding_vector", Vector(64), nullable=True),
    )

    op.execute(
        """
        UPDATE retrieval_documents
        SET embedding_vector = (
            (
                '[' ||
                array_to_string(
                    ARRAY(
                        SELECT jsonb_array_elements_text(embedding_vector_json::jsonb)
                    ),
                    ','
                ) ||
                ']'
            )::vector
        )
        WHERE embedding_vector_json IS NOT NULL
          AND embedding_vector IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("retrieval_documents", "embedding_vector")