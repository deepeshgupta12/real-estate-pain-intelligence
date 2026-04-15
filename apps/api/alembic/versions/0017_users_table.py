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
  2. Use sqlalchemy.dialects.postgresql.ENUM (not sa.Enum) with create_type=False
     — this is the ONLY type that fully suppresses SQLAlchemy's before_create
     event hook.  sa.Enum is the generic cross-database type; it ignores
     create_type=False and always fires before_create.
  3. inspect(bind).has_table() — skips the CREATE TABLE block entirely if the
     table already exists.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

revision = "0017_users_table"
down_revision = "0016_retrieval_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: create the enum type if it doesn't already exist.
    # DO $$ EXCEPTION block works on ALL PostgreSQL versions (9.x–16+).
    op.execute(text("""
        DO $$ BEGIN
            CREATE TYPE user_role_enum AS ENUM ('admin', 'analyst', 'viewer');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    # Step 2: create the users table only when it doesn't already exist.
    # IMPORTANT: use PgEnum (sqlalchemy.dialects.postgresql.ENUM) with
    # create_type=False — NOT sa.Enum.  sa.Enum ignores create_type=False
    # and fires a bare CREATE TYPE via its before_create event, which raises
    # DuplicateObject when the type already exists.  PgEnum fully respects
    # create_type=False and skips the CREATE TYPE entirely.
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
                PgEnum("admin", "analyst", "viewer", name="user_role_enum", create_type=False),
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
