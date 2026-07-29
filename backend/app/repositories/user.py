from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_exceptions import EmailAlreadyRegisteredError
from app.models.user import User


def _is_unique_constraint_violation(
    exc: IntegrityError,
    constraint_name: str,
) -> bool:
    orig = exc.orig
    if orig is None:
        return False
    if hasattr(orig, "constraint_name"):
        return orig.constraint_name == constraint_name
    return constraint_name in str(orig)


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        user_id: uuid.UUID | None = None,
    ) -> User:
        user = User(email=email, password_hash=password_hash)
        if user_id is not None:
            user.id = user_id
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if _is_unique_constraint_violation(exc, "uq_users_email"):
                raise EmailAlreadyRegisteredError() from exc
            raise
        return user
