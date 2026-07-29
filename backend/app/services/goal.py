from __future__ import annotations

import uuid

from app.core.goal_exceptions import GoalNotFoundError
from app.models.goal import Goal
from app.repositories.goal import GoalRepository
from app.schemas.goals import GoalCreate, GoalUpdate


class GoalService:
    """Service for goal business logic.

    Encapsulates user-scoped goal listing, lookup, creation, update, and
    deletion workflows.  Does not commit, flush, roll back, or close the
    session.
    """

    def __init__(self, repository: GoalRepository) -> None:
        self._repository = repository

    async def list_goals(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[Goal]:
        """List goals for one user in descending created_at order."""
        return await self._repository.list_by_user_id(user_id=user_id)

    async def get_goal(
        self,
        *,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> Goal:
        """Retrieve a single goal by user and goal ID.

        Raises ``GoalNotFoundError`` when the goal does not exist or is not
        owned by the user.
        """
        orm_goal = await self._repository.get_by_user_and_id(
            user_id=user_id,
            goal_id=goal_id,
        )
        if orm_goal is None:
            raise GoalNotFoundError()
        return orm_goal

    async def create_goal(
        self,
        *,
        user_id: uuid.UUID,
        data: GoalCreate,
    ) -> Goal:
        """Create a goal for the given user.

        Delegates persistence to the repository.
        """
        return await self._repository.create(user_id=user_id, data=data)

    async def update_goal(
        self,
        *,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
        data: GoalUpdate,
    ) -> Goal:
        """Update a goal owned by the given user.

        Loads the goal using both user_id and goal_id, raises
        ``GoalNotFoundError`` when absent, and applies the PATCH data.
        """
        orm_goal = await self._repository.get_by_user_and_id(
            user_id=user_id,
            goal_id=goal_id,
        )
        if orm_goal is None:
            raise GoalNotFoundError()
        return await self._repository.update(goal=orm_goal, data=data)

    async def delete_goal(
        self,
        *,
        user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> None:
        """Delete a goal owned by the given user.

        Verifies ownership by querying with both user_id and goal_id,
        raises ``GoalNotFoundError`` when absent, and passes the loaded ORM
        object to the repository delete.
        """
        orm_goal = await self._repository.get_by_user_and_id(
            user_id=user_id,
            goal_id=goal_id,
        )
        if orm_goal is None:
            raise GoalNotFoundError()
        await self._repository.delete(goal=orm_goal)
