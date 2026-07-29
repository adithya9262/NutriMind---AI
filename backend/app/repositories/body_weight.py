from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.body_weight_exceptions import (
    DuplicateBodyWeightDateError,
    DuplicateBodyWeightEntryIdError,
)
from app.models.body_weight import BodyWeight


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


class BodyWeightRepository:
    """Repository for BodyWeight database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user_id(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[BodyWeight]:
        """List body-weight entries for one user.

        Returns entries ordered by logged_date descending, then entry_id
        ascending as a deterministic tie-breaker.
        Returns an empty list when no entries exist.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = (
            select(BodyWeight)
            .where(BodyWeight.user_id == user_id)
            .order_by(BodyWeight.logged_date.desc(), BodyWeight.entry_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_entry_id(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> BodyWeight | None:
        """Look up a body-weight entry by both user_id and entry_id.

        Returns the BodyWeight when found, or None when not found.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = (
            select(BodyWeight)
            .where(BodyWeight.user_id == user_id)
            .where(BodyWeight.entry_id == entry_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
        logged_date: date,
        weight_kg: Decimal,
    ) -> BodyWeight:
        """Create and persist a new body-weight entry.

        Accepts only trusted explicit values.
        Adds the BodyWeight to the session and flushes.
        The caller owns transaction commit/rollback.

        Raises ``DuplicateBodyWeightDateError`` on duplicate
        (user_id, logged_date).
        Raises ``DuplicateBodyWeightEntryIdError`` on duplicate
        (user_id, entry_id).
        """
        entry = BodyWeight(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=logged_date,
            weight_kg=weight_kg,
        )
        self._session.add(entry)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if _is_unique_constraint_violation(exc, "uq_body_weights_user_id_logged_date"):
                raise DuplicateBodyWeightDateError() from exc
            if _is_unique_constraint_violation(exc, "uq_body_weights_user_id_entry_id"):
                raise DuplicateBodyWeightEntryIdError() from exc
            raise
        return entry

    async def delete(
        self,
        *,
        entry: BodyWeight,
    ) -> None:
        """Delete an existing body-weight entry.

        Deletes the exact supplied ORM entry and flushes.
        The caller owns transaction commit/rollback.
        """
        await self._session.delete(entry)
        await self._session.flush()
