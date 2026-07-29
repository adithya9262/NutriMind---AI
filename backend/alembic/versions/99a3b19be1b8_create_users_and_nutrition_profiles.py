"""create users and nutrition profiles

Revision ID: 99a3b19be1b8
Revises: 3f0c6eb4f49e
Create Date: 2026-07-11 20:17:35.413279
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "99a3b19be1b8"
down_revision: str | None = "3f0c6eb4f49e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "nutrition_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column(
            "biological_sex",
            sa.Enum(
                "male",
                "female",
                "other",
                "prefer_not_to_say",
                name="biological_sex",
            ),
            nullable=False,
        ),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "activity_level",
            sa.Enum(
                "sedentary",
                "lightly_active",
                "moderately_active",
                "very_active",
                "extra_active",
                name="activity_level",
            ),
            nullable=False,
        ),
        sa.Column(
            "goal",
            sa.Enum(
                "lose_weight",
                "maintain_weight",
                "gain_weight",
                "gain_muscle",
                name="nutrition_goal",
            ),
            nullable=False,
        ),
        sa.Column(
            "target_weight_kg",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
        sa.Column(
            "dietary_preference",
            sa.Enum(
                "no_preference",
                "vegetarian",
                "vegan",
                "pescatarian",
                "eggetarian",
                name="dietary_preference",
            ),
            nullable=True,
        ),
        sa.Column(
            "allergies",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
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
            "height_cm >= 50 AND height_cm <= 300",
            name="ck_nutrition_profiles_height_cm_range",
        ),
        sa.CheckConstraint(
            "target_weight_kg IS NULL OR (target_weight_kg >= 10 AND target_weight_kg <= 700)",
            name="ck_nutrition_profiles_target_weight_kg_range",
        ),
        sa.CheckConstraint(
            "weight_kg >= 10 AND weight_kg <= 700",
            name="ck_nutrition_profiles_weight_kg_range",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_nutrition_profiles_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_nutrition_profiles_user_id"),
    )


def downgrade() -> None:
    op.drop_table("nutrition_profiles")
    op.drop_table("users")
    # Drop enum types after their dependent tables are removed.
    # Each type was created implicitly by op.create_table on upgrade.
    op.execute(sa.text("DROP TYPE IF EXISTS dietary_preference"))
    op.execute(sa.text("DROP TYPE IF EXISTS nutrition_goal"))
    op.execute(sa.text("DROP TYPE IF EXISTS activity_level"))
    op.execute(sa.text("DROP TYPE IF EXISTS biological_sex"))
