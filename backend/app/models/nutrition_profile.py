from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.enums import (
    ActivityLevel,
    BiologicalSex,
    DietaryPreference,
    FitnessGoal,
    NutritionGoal,
)
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class NutritionProfile(Base, TimestampMixin):
    __tablename__ = "nutrition_profiles"

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_nutrition_profiles_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", name="uq_nutrition_profiles_user_id"),
        sa.CheckConstraint(
            "height_cm >= 50 AND height_cm <= 300",
            name="ck_nutrition_profiles_height_cm_range",
        ),
        sa.CheckConstraint(
            "weight_kg >= 10 AND weight_kg <= 700",
            name="ck_nutrition_profiles_weight_kg_range",
        ),
        sa.CheckConstraint(
            "target_weight_kg IS NULL OR (target_weight_kg >= 10 AND target_weight_kg <= 700)",
            name="ck_nutrition_profiles_target_weight_kg_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        sa.Date,
        nullable=True,
    )
    biological_sex: Mapped[BiologicalSex | None] = mapped_column(
        sa.Enum(
            BiologicalSex, name="biological_sex", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
    )
    height_cm: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(5, 2),
        nullable=True,
    )
    weight_kg: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(5, 2),
        nullable=True,
    )
    activity_level: Mapped[ActivityLevel | None] = mapped_column(
        sa.Enum(
            ActivityLevel, name="activity_level", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
    )
    goal: Mapped[NutritionGoal | None] = mapped_column(
        sa.Enum(
            NutritionGoal, name="nutrition_goal", values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True,
    )
    target_weight_kg: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(5, 2),
        nullable=True,
    )
    dietary_preference: Mapped[DietaryPreference | None] = mapped_column(
        sa.Enum(
            DietaryPreference,
            name="dietary_preference",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )
    allergies: Mapped[list[str] | None] = mapped_column(
        JSONB,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
        nullable=True,
    )

    full_name: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    fitness_goal: Mapped[FitnessGoal | None] = mapped_column(
        sa.Enum(FitnessGoal, name="fitness_goal", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    medical_conditions: Mapped[list[str] | None] = mapped_column(
        JSONB,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
        nullable=True,
    )
    water_goal_ml: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    sleep_goal_hours: Mapped[Decimal | None] = mapped_column(sa.Numeric(4, 2), nullable=True)
    daily_calorie_goal: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    daily_protein_goal_g: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    daily_carb_goal_g: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    daily_fat_goal_g: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    user: Mapped[User] = relationship(
        back_populates="nutrition_profile",
    )
