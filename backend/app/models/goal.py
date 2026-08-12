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
from app.models.enums import GoalStatus, GoalType
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_goals_user_id",
            ondelete="CASCADE",
        ),
        sa.Index("ix_goals_user_id_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )
    goal_type: Mapped[GoalType] = mapped_column(
        sa.Enum(GoalType, name="goal_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        sa.String(200),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        sa.String(2000),
        nullable=True,
    )
    status: Mapped[GoalStatus] = mapped_column(
        sa.Enum(GoalStatus, name="goal_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=GoalStatus.ACTIVE,
    )
    start_date: Mapped[date | None] = mapped_column(
        sa.Date,
        nullable=True,
    )
    end_date: Mapped[date | None] = mapped_column(
        sa.Date,
        nullable=True,
    )
    weekly_target: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(7, 2),
        nullable=True,
    )
    target_calories: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
    )
    target_protein_g: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
    )
    target_carbs_g: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
    )
    target_fats_g: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
    )
    target_water_ml: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
    )
    progress_percentage: Mapped[Decimal | None] = mapped_column(
        sa.Numeric(5, 2),
        default=Decimal("0"),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="goals",
    )
