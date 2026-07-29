"""create body weights

Revision ID: e5f6a7b8c9d0
Revises: b8a7c3d9e1f2
Create Date: 2026-07-12 13:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "b8a7c3d9e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "body_weights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("entry_id", sa.Uuid(), nullable=False),
        sa.Column("logged_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_body_weights_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "logged_date",
            name="uq_body_weights_user_id_logged_date",
        ),
        sa.UniqueConstraint(
            "user_id",
            "entry_id",
            name="uq_body_weights_user_id_entry_id",
        ),
        sa.CheckConstraint(
            "weight_kg >= 10.00 AND weight_kg <= 700.00",
            name="ck_body_weights_weight_kg_range",
        ),
    )


def downgrade() -> None:
    op.drop_table("body_weights")
