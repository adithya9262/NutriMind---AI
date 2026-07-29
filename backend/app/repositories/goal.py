from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.schemas.goals import GoalCreate, GoalUpdate


class GoalRepository:
    """Repository for Goal database operations.

    Encapsulates user-scoped reads, creation, mutation, and deletion of
    goal rows.  Does not commit, roll back, or close the session; the
    caller owns transaction boundaries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user_id(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[Goal]:
        """List goals for one user.

        Returns all goals owned by ``user_id`` ordered by created_at descending.
        Returns an empty list when no goals exist.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = (
            select(Goal)
            .where(Goal.user_id == user_id)
            .order_by(Goal.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_id(
        self,
        *,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> Goal | None:
        """Look up a goal by both user_id and goal id.

        Returns the Goal ORM object when found, or None when not found or
        when the goal is owned by a different user.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = select(Goal).where(Goal.user_id == user_id).where(Goal.id == goal_id)
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        data: GoalCreate,
    ) -> Goal:
        """Create and persist a new goal.

        Accepts a trusted user_id and a validated GoalCreate schema.
        Adds the Goal to the session and flushes.
        The caller owns transaction commit/rollback.
        """
        orm_goal = Goal(
            user_id=user_id,
            goal_type=data.goal_type,
            title=data.title,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            weekly_target=data.weekly_target,
            target_calories=data.target_calories,
            target_protein_g=data.target_protein_g,
            target_carbs_g=data.target_carbs_g,
            target_fats_g=data.target_fats_g,
            target_water_ml=data.target_water_ml,
        )
        self._session.add(orm_goal)
        await self._session.flush()
        return orm_goal

    async def update(
        self,
        goal: Goal,
        data: GoalUpdate,
    ) -> Goal:
        """Update an existing goal using PATCH semantics.

        Only fields explicitly supplied in the PATCH schema are updated.
        Omitted fields remain unchanged.
        The caller owns transaction commit/rollback.
        """
        for field in data.model_fields_set:
            value = getattr(data, field)
            setattr(goal, field, value)
        if data.model_fields_set:
            await self._session.flush()
        return goal

    async def delete(
        self,
        *,
        goal: Goal,
    ) -> None:
        """Delete an existing goal.

        Deletes the exact supplied ORM object and flushes.
        The caller owns transaction commit/rollback.
        """
        await self._session.delete(goal)
        await self._session.flush()
