"""create tasks

Revision ID: a7b8c9d0e5f
Revises: e5f6a7b8c9d0
Create Date: 2026-07-13 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7b8c9d0e5f"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", name="task_priority"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "completed", name="task_status"),
            nullable=False,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            "(status = 'pending' AND completed_at IS NULL) "
            "OR (status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_tasks_status_completed_at_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_tasks_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "task_id",
            name="uq_tasks_user_id_task_id",
        ),
    )
    op.create_index(
        "ix_tasks_user_id_status_due_date",
        "tasks",
        ["user_id", "status", "due_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_user_id_status_due_date")
    op.drop_table("tasks")
    # Drop enum types after their dependent table is removed.
    op.execute(sa.text("DROP TYPE IF EXISTS task_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS task_priority"))
