from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nutrition_log_exceptions import (
    NutritionLogEntryAlreadyExistsError,
)
from app.core.nutrition_logs import MealType
from app.models.nutrition_log import NutritionLog
from app.schemas.nutrition_logs import NutritionLogEntryCreate


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


_MEAL_TYPE_ORDER_CASE = case(
    (NutritionLog.meal_type == MealType.BREAKFAST, 0),
    (NutritionLog.meal_type == MealType.LUNCH, 1),
    (NutritionLog.meal_type == MealType.DINNER, 2),
    (NutritionLog.meal_type == MealType.SNACK, 3),
    else_=4,
)


class NutritionLogRepository:
    """Repository for NutritionLog database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user_and_date(
        self,
        *,
        user_id: uuid.UUID,
        logged_date: date,
    ) -> list[NutritionLog]:
        """List nutrition-log entries for one user on one explicit date.

        Returns entries ordered by meal type (breakfast, lunch, dinner, snack),
        then created_at ascending, then id ascending as final tie-breaker.
        Returns an empty list when no entries exist.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = (
            select(NutritionLog)
            .where(NutritionLog.user_id == user_id)
            .where(NutritionLog.logged_date == logged_date)
            .order_by(_MEAL_TYPE_ORDER_CASE, NutritionLog.created_at, NutritionLog.id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_entry_id(
        self,
        *,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
    ) -> NutritionLog | None:
        """Look up an entry by both user_id and entry_id.

        Returns the NutritionLog when found, or None when not found.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = (
            select(NutritionLog)
            .where(NutritionLog.user_id == user_id)
            .where(NutritionLog.entry_id == entry_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        logged_date: date,
        data: NutritionLogEntryCreate,
    ) -> NutritionLog:
        """Create and persist a new nutrition-log entry.

        Accepts a trusted user_id, an explicit logged_date, and a validated
        NutritionLogEntryCreate schema.  Adds the NutritionLog to the session
        and flushes.  The caller owns transaction commit/rollback.

        Raises ``NutritionLogEntryAlreadyExistsError`` on duplicate
        (user_id, entry_id).
        """
        entry = NutritionLog(
            user_id=user_id,
            logged_date=logged_date,
            entry_id=data.entry_id,
            food_name=data.food_name,
            meal_type=data.meal_type,
            serving_description=data.serving_description,
            calories_kcal=data.calories_kcal,
            protein_g=data.protein_g,
            carbohydrate_g=data.carbohydrate_g,
            fat_g=data.fat_g,
        )
        self._session.add(entry)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if _is_unique_constraint_violation(exc, "uq_nutrition_logs_user_id_entry_id"):
                raise NutritionLogEntryAlreadyExistsError() from exc
            raise
        return entry

    async def delete(
        self,
        *,
        entry: NutritionLog,
    ) -> None:
        """Delete an existing nutrition-log entry.

        Deletes the exact supplied ORM entry and flushes.
        The caller owns transaction commit/rollback.
        """
        await self._session.delete(entry)
        await self._session.flush()
