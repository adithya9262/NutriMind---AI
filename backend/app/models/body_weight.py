from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class BodyWeight(Base, TimestampMixin):
    __tablename__ = "body_weights"

    __table_args__ = (
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

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
    )
    logged_date: Mapped[date] = mapped_column(
        sa.Date,
        nullable=False,
    )
    weight_kg: Mapped[Decimal] = mapped_column(
        sa.Numeric(5, 2),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="body_weights",
    )
