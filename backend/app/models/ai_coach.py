import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Date, ForeignKey, String, Text, Integer, Float, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ChatRole
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ChatSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    pinned: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, server_default="false")
    archived: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, server_default="false")
    # Tracks when the last message was sent — used for "sort by latest activity"
    last_active_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, index=True
    )
    # Cached count updated on every message insert to avoid COUNT(*) on list
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[ChatRole] = mapped_column(SQLEnum(ChatRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Average response time in ms tracked per assistant message (null for user msgs)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Feedback tracking
    is_helpful: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)
    is_not_helpful: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)
    was_regenerated: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, server_default="false")
    was_copied: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, server_default="false")

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class AIUsageTracker(Base, UUIDMixin, TimestampMixin):
    """One row per user per UTC calendar day. The unique constraint enables
    INSERT ... ON CONFLICT DO UPDATE for atomic upsert / auto-daily-reset."""

    __tablename__ = "ai_usage_trackers"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_ai_usage_user_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    messages_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    images_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    meal_plans_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ai_usage_trackers")


class AIUserMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_user_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. preference, allergy, habit, goal
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    last_used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Embedding stored as JSONB for local vector math fallback without pgvector
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ai_memories")
