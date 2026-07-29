from __future__ import annotations

import uuid
from datetime import date

from app.core.nutrition_log_exceptions import NutritionLogEntryNotFoundError
from app.models.nutrition_log import NutritionLog
from app.repositories.nutrition_log import NutritionLogRepository
from app.schemas.nutrition_logs import NutritionLogEntryCreate


class NutritionLogService:
    """Service for nutrition-log business logic.

    Encapsulates daily-entry listing, creation, and deletion workflows.
    Does not commit, flush, roll back, or close the session.
    """

    def __init__(self, repository: NutritionLogRepository) -> None:
        self._repository = repository

    async def list_daily_entries(
        self,
        *,
        user_id: uuid.UUID,
        logged_date: date,
    ) -> list[NutritionLog]:
        """List nutrition-log entries for one user on an explicit date.

        Delegates to the repository.  Returns the repository result
        unchanged.  Does not compute totals or match against goals.
        """
        return await self._repository.list_by_user_and_date(
            user_id=user_id,
            logged_date=logged_date,
        )

    async def create_entry(
        self,
        *,
        user_id: uuid.UUID,
        logged_date: date,
        data: NutritionLogEntryCreate,
    ) -> NutritionLog:
        """Create a nutrition-log entry for the given user and date.

        Delegates to the repository.  Preserves domain exceptions.
        Does not transform, enrich, or derive nutrition values.
        """
        return await self._repository.create(
            user_id=user_id,
            logged_date=logged_date,
            data=data,
        )

    async def delete_entry(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> None:
        """Delete a nutrition-log entry owned by the given user.

        Verifies ownership by querying with both user_id and entry_id.
        Raises ``NutritionLogEntryNotFoundError`` when the entry does
        not exist or is not owned by the user.
        """
        entry = await self._repository.get_by_user_and_entry_id(
            user_id=user_id,
            entry_id=entry_id,
        )
        if entry is None:
            raise NutritionLogEntryNotFoundError()
        await self._repository.delete(entry=entry)
