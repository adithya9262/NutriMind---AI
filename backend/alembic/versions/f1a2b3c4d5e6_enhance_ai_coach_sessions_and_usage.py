"""Enhance AI Coach sessions and usage tracker

Adds last_active_at, message_count to chat_sessions;
adds response_time_ms to chat_messages;
adds unique constraint (user_id, usage_date) to ai_usage_trackers.

Revision ID: f1a2b3c4d5e6
Revises: 028b646fc50a
Create Date: 2026-07-22 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "028b646fc50a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # chat_sessions: add last_active_at and message_count
    op.add_column(
        "chat_sessions",
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_chat_sessions_last_active_at",
        "chat_sessions",
        ["last_active_at"],
        unique=False,
    )

    # chat_messages: add response_time_ms
    op.add_column(
        "chat_messages",
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
    )

    # ai_usage_trackers: add unique constraint (user_id, usage_date)
    # First remove any duplicate rows keeping the latest one
    op.execute("""
        DELETE FROM ai_usage_trackers a
        USING ai_usage_trackers b
        WHERE a.usage_date = b.usage_date
          AND a.user_id = b.user_id
          AND a.created_at < b.created_at
    """)
    op.create_unique_constraint(
        "uq_ai_usage_user_date",
        "ai_usage_trackers",
        ["user_id", "usage_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_ai_usage_user_date", "ai_usage_trackers", type_="unique")
    op.drop_column("chat_messages", "response_time_ms")
    op.drop_index("ix_chat_sessions_last_active_at", table_name="chat_sessions")
    op.drop_column("chat_sessions", "message_count")
    op.drop_column("chat_sessions", "last_active_at")
