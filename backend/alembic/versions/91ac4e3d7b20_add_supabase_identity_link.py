"""Add an explicit Supabase identity link to users.

Revision ID: 91ac4e3d7b20
Revises: 9d331b5a060d
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "91ac4e3d7b20"
down_revision: str | None = "9d331b5a060d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("supabase_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_users_supabase_user_id",
        "users",
        ["supabase_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_supabase_user_id", table_name="users")
    op.drop_column("users", "supabase_user_id")
