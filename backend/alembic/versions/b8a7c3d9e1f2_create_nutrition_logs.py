"""create nutrition logs

Revision ID: b8a7c3d9e1f2
Revises: 99a3b19be1b8
Create Date: 2026-07-12 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8a7c3d9e1f2"
down_revision: str | None = "99a3b19be1b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nutrition_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("logged_date", sa.Date(), nullable=False),
        sa.Column("entry_id", sa.Uuid(), nullable=False),
        sa.Column("food_name", sa.String(length=200), nullable=False),
        sa.Column(
            "meal_type",
            sa.Enum(
                "breakfast",
                "lunch",
                "dinner",
                "snack",
                name="meal_type",
            ),
            nullable=False,
        ),
        sa.Column("serving_description", sa.String(length=200), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("carbohydrate_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=6, scale=2), nullable=False),
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
        sa.CheckConstraint(
            "calories_kcal >= 0 AND calories_kcal <= 10000",
            name="ck_nutrition_logs_calories_kcal_range",
        ),
        sa.CheckConstraint(
            "protein_g >= 0 AND protein_g <= 1000",
            name="ck_nutrition_logs_protein_g_range",
        ),
        sa.CheckConstraint(
            "carbohydrate_g >= 0 AND carbohydrate_g <= 2000",
            name="ck_nutrition_logs_carbohydrate_g_range",
        ),
        sa.CheckConstraint(
            "fat_g >= 0 AND fat_g <= 1000",
            name="ck_nutrition_logs_fat_g_range",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_nutrition_logs_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "entry_id", name="uq_nutrition_logs_user_id_entry_id"),
    )
    op.create_index(
        "ix_nutrition_logs_user_id_logged_date",
        "nutrition_logs",
        ["user_id", "logged_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_nutrition_logs_user_id_logged_date")
    op.drop_table("nutrition_logs")
    op.execute(sa.text("DROP TYPE IF EXISTS meal_type"))
