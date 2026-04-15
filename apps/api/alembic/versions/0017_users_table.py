"""Add users table for JWT authentication

Revision ID: 0017_users_table
Revises: 0016_retrieval_pgvector
Create Date: 2026-04-13

Note: made fully idempotent because this migration was partially applied
while the chain was broken at 0018 (0018 referenced a non-existent parent).
The enum and table were created in the DB but alembic_version never recorded
0017 as applied.

Guard strategy:
  1. DO $$ ... EXCEPTION WHEN duplicate_object THEN NULL $$ block to create
     the enum type — works on ALL PostgreSQL versions (unlike CREATE TYPE
     IF NOT EXISTS which requires PG 12+).
  2. create_type=False on sa.Enum — prevents SQLAlchemy from firing a second
     CREATE TYPE via its before_create event hook when op.create_table runs.
  3. inspect(bind).has_table() — skips the CREATE TABLE block entirely if the
     table already exists.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "0017_users_table"
down_revision = "0016_retrieval_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: create the enum type if it doesn't already exist.
    # We use a PL/pgSQL DO block with EXCEPTION handling instead of
    # "CREATE TYPE IF NOT EXISTS" because that syntax requires PG 12+.
    # This DO block works on PG 9.x, 10, 11, 12, 13, 14, 15, 16+.
    op.execute(text("""
        DO $$ BEGIN
            CREATE TYPE user_role_enum AS ENUM ('admin', 'analyst', 'viewer');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    # Step 2: create the users table only when it doesn't already exist.
    # create_type=False on the Enum column suppresses the SQLAlchemy
    # before_create hook that would otherwise fire a second CREATE TYPE.
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
        op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute(text("""
        DO $$ BEGIN
            DROP TYPE user_role_enum;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
    """))
