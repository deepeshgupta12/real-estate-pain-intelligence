"""Add users table for JWT authentication

Revision ID: 0017_users_table
Revises: 0016_retrieval_pgvector
Create Date: 2026-04-13

Note: made fully idempotent because this migration was partially applied
while the chain was broken at 0018 (0018 referenced a non-existent parent).
The enum and table were created in the DB but alembic_version never recorded
0017 as applied.  Two-layer guard:
  1. CREATE TYPE IF NOT EXISTS — PostgreSQL-native, safe to re-run.
  2. create_type=False on sa.Enum — prevents SQLAlchemy from firing a
     second CREATE TYPE as a before_create event when op.create_table runs.
  3. inspector.has_table() check — skips the whole CREATE TABLE block if
     the table already exists.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0017_users_table"
down_revision = "0016_retrieval_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: ensure the enum type exists.  IF NOT EXISTS is safe on PG 9.1+.
    op.execute(
        "CREATE TYPE IF NOT EXISTS user_role_enum AS ENUM ('admin', 'analyst', 'viewer')"
    )

    # Step 2: create the users table only when it doesn't already exist.
    # We use create_type=False on the Enum column so SQLAlchemy does NOT fire
    # a second "CREATE TYPE user_role_enum" via its before_create event hook —
    # we've already handled the type creation above.
    bind = op.get_bind()
    if not inspect(bind).has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=True),
            sa.Column(
                "role",
                # create_type=False: type already created above; don't let
                # SQLAlchemy try to CREATE TYPE again during table creation.
                sa.Enum("admin", "analyst", "viewer", name="user_role_enum", create_type=False),
                nullable=False,
                server_default="analyst",
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        # Create the index only when the table was just created.
        op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
