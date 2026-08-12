from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, Uuid

from app.core.tasks import (
    MAX_TASK_DESCRIPTION_LENGTH,
    MAX_TASK_TITLE_LENGTH,
    TaskCategory,
    TaskPriority,
    TaskRecurrence,
    TaskStatus,
)
from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_tasks_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "task_id",
            name="uq_tasks_user_id_task_id",
        ),
        sa.CheckConstraint(
            "(status = 'pending' AND completed_at IS NULL) "
            "OR (status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_tasks_status_completed_at_consistency",
        ),
        sa.Index(
            "ix_tasks_user_id_status_due_date",
            "user_id",
            "status",
            "due_date",
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
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        sa.String(MAX_TASK_TITLE_LENGTH),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        sa.String(MAX_TASK_DESCRIPTION_LENGTH),
        nullable=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        sa.Enum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        sa.Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(
        sa.Date(),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    category: Mapped[TaskCategory] = mapped_column(
        sa.Enum(
            TaskCategory,
            name="task_category",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default="custom",
    )
    recurrence: Mapped[TaskRecurrence] = mapped_column(
        sa.Enum(
            TaskRecurrence,
            name="task_recurrence",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default="none",
    )

    user: Mapped[User] = relationship(
        back_populates="tasks",
    )
