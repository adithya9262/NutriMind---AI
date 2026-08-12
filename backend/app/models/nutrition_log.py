from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.nutrition_logs import (
    MAX_CALORIES_KCAL,
    MAX_CARBOHYDRATE_G,
    MAX_FAT_G,
    MAX_PROTEIN_G,
    MealType,
)
from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class NutritionLog(Base, TimestampMixin):
    __tablename__ = "nutrition_logs"

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_nutrition_logs_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "entry_id", name="uq_nutrition_logs_user_id_entry_id"),
        sa.CheckConstraint(
            f"calories_kcal >= 0 AND calories_kcal <= {MAX_CALORIES_KCAL}",
            name="ck_nutrition_logs_calories_kcal_range",
        ),
        sa.CheckConstraint(
            f"protein_g >= 0 AND protein_g <= {MAX_PROTEIN_G}",
            name="ck_nutrition_logs_protein_g_range",
        ),
        sa.CheckConstraint(
            f"carbohydrate_g >= 0 AND carbohydrate_g <= {MAX_CARBOHYDRATE_G}",
            name="ck_nutrition_logs_carbohydrate_g_range",
        ),
        sa.CheckConstraint(
            f"fat_g >= 0 AND fat_g <= {MAX_FAT_G}",
            name="ck_nutrition_logs_fat_g_range",
        ),
        sa.Index("ix_nutrition_logs_user_id_logged_date", "user_id", "logged_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )
    logged_date: Mapped[date] = mapped_column(
        sa.Date,
        nullable=False,
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
    )
    food_name: Mapped[str] = mapped_column(
        sa.String(200),
        nullable=False,
    )
    meal_type: Mapped[MealType] = mapped_column(
        sa.Enum(MealType, name="meal_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    serving_description: Mapped[str] = mapped_column(
        sa.String(200),
        nullable=False,
    )
    calories_kcal: Mapped[Decimal] = mapped_column(
        sa.Numeric(7, 2),
        nullable=False,
    )
    protein_g: Mapped[Decimal] = mapped_column(
        sa.Numeric(6, 2),
        nullable=False,
    )
    carbohydrate_g: Mapped[Decimal] = mapped_column(
        sa.Numeric(6, 2),
        nullable=False,
    )
    fat_g: Mapped[Decimal] = mapped_column(
        sa.Numeric(6, 2),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="nutrition_logs",
    )
