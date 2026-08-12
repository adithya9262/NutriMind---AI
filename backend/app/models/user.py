from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.body_weight import BodyWeight
    from app.models.goal import Goal
    from app.models.nutrition_log import NutritionLog
    from app.models.nutrition_profile import NutritionProfile
    from app.models.task import Task
    from app.models.ai_coach import ChatSession, AIUsageTracker, AIUserMemory


class User(Base, TimestampMixin):
    __tablename__ = "users"

    __table_args__ = (sa.UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        sa.String(320),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        sa.String(128),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=True,
        server_default=sa.text("true"),
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
        server_default=sa.text("false"),
        nullable=False,
    )

    nutrition_profile: Mapped[NutritionProfile | None] = relationship(
        "NutritionProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    nutrition_logs: Mapped[list[NutritionLog]] = relationship(
        "NutritionLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    body_weights: Mapped[list[BodyWeight]] = relationship(
        "BodyWeight",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tasks: Mapped[list[Task]] = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    goals: Mapped[list[Goal]] = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    ai_usage_trackers: Mapped[list["AIUsageTracker"]] = relationship(
        "AIUsageTracker",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    ai_memories: Mapped[list["AIUserMemory"]] = relationship(
        "AIUserMemory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
