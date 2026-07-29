from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.core.body_weight_exceptions import BodyWeightNotFoundError
from app.models.body_weight import BodyWeight
from app.repositories.body_weight import BodyWeightRepository


class BodyWeightService:
    """Service for body-weight business logic.

    Encapsulates history listing, entry lookup, creation, and deletion
    workflows.  Does not commit, flush, roll back, or close the session.
    """

    def __init__(self, repository: BodyWeightRepository) -> None:
        self._repository = repository

    async def list_history(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[BodyWeight]:
        """List body-weight entries for one user.

        Delegates to the repository.  Returns the repository result
        unchanged.  Preserves repository ordering.
        """
        return await self._repository.list_by_user_id(user_id=user_id)

    async def get_entry(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> BodyWeight:
        """Retrieve a single body-weight entry by user and entry ID.

        Raises ``BodyWeightNotFoundError`` when the entry does not exist
        or is not owned by the user.
        """
        entry = await self._repository.get_by_user_and_entry_id(
            user_id=user_id,
            entry_id=entry_id,
        )
        if entry is None:
            raise BodyWeightNotFoundError()
        return entry

    async def create_entry(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
        logged_date: date,
        weight_kg: Decimal,
    ) -> BodyWeight:
        """Create a body-weight entry for the given user.

        Delegates to the repository.  Preserves domain exceptions.
        Does not transform, enrich, or derive body-weight values.
        """
        return await self._repository.create(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=logged_date,
            weight_kg=weight_kg,
        )

    async def delete_entry(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> None:
        """Delete a body-weight entry owned by the given user.

        Verifies ownership by querying with both user_id and entry_id.
        Raises ``BodyWeightNotFoundError`` when the entry does not
        exist or is not owned by the user.
        """
        entry = await self._repository.get_by_user_and_entry_id(
            user_id=user_id,
            entry_id=entry_id,
        )
        if entry is None:
            raise BodyWeightNotFoundError()
        await self._repository.delete(entry=entry)
