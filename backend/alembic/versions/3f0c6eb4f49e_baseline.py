"""baseline

Establishes Alembic migration history before any ORM business models
are introduced. No application tables are created or dropped.

Revision ID: 3f0c6eb4f49e
Revises:
Create Date: 2026-07-11 19:54:56.788790
"""

revision: str = "3f0c6eb4f49e"
down_revision: str | None = None
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
