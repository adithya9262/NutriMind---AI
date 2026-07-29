"""add goals and profile fields

Revision ID: b9c8d7e6f5a0
Revises: a7b8c9d0e5f
Create Date: 2026-07-20 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b9c8d7e6f5a0"
down_revision: str | None = "a7b8c9d0e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE fitness_goal AS ENUM ('weight_loss','weight_gain','maintain_weight','muscle_gain','fat_loss','custom','general_fitness')"))
    op.add_column(
        "nutrition_profiles",
        sa.Column("full_name", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("phone", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column(
            "fitness_goal",
            sa.Enum(
                "weight_loss",
                "weight_gain",
                "maintain_weight",
                "muscle_gain",
                "fat_loss",
                "custom",
                "general_fitness",
                name="fitness_goal",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column(
            "medical_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("water_goal_ml", sa.Integer(), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column(
            "sleep_goal_hours", sa.Numeric(precision=4, scale=2), nullable=True
        ),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("daily_calorie_goal", sa.Integer(), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("daily_protein_goal_g", sa.Integer(), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("daily_carb_goal_g", sa.Integer(), nullable=True),
    )
    op.add_column(
        "nutrition_profiles",
        sa.Column("daily_fat_goal_g", sa.Integer(), nullable=True),
    )

    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "goal_type",
            sa.Enum(
                "weight_loss",
                "weight_gain",
                "maintain_weight",
                "muscle_gain",
                "fat_loss",
                "custom",
                name="goal_type",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "active", "completed", "cancelled", "paused", name="goal_status"
            ),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "weekly_target", sa.Numeric(precision=7, scale=2), nullable=True
        ),
        sa.Column("target_calories", sa.Integer(), nullable=True),
        sa.Column("target_protein_g", sa.Integer(), nullable=True),
        sa.Column("target_carbs_g", sa.Integer(), nullable=True),
        sa.Column("target_fats_g", sa.Integer(), nullable=True),
        sa.Column("target_water_ml", sa.Integer(), nullable=True),
        sa.Column(
            "progress_percentage",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_goals_user_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_goals_user_id_status", "goals", ["user_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_goals_user_id_status")
    op.drop_table("goals")

    op.execute(sa.text("DROP TYPE IF EXISTS goal_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS goal_type"))
    op.execute(sa.text("DROP TYPE IF EXISTS fitness_goal"))

    op.drop_column("nutrition_profiles", "daily_fat_goal_g")
    op.drop_column("nutrition_profiles", "daily_carb_goal_g")
    op.drop_column("nutrition_profiles", "daily_protein_goal_g")
    op.drop_column("nutrition_profiles", "daily_calorie_goal")
    op.drop_column("nutrition_profiles", "sleep_goal_hours")
    op.drop_column("nutrition_profiles", "water_goal_ml")
    op.drop_column("nutrition_profiles", "medical_conditions")
    op.drop_column("nutrition_profiles", "fitness_goal")
    op.drop_column("nutrition_profiles", "avatar_url")
    op.drop_column("nutrition_profiles", "phone")
    op.drop_column("nutrition_profiles", "full_name")
