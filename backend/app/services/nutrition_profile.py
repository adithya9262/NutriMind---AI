from __future__ import annotations

import uuid

from app.core.nutrition_profile_exceptions import (
    NutritionProfileAlreadyExistsError,
    NutritionProfileNotFoundError,
)
from app.models.nutrition_profile import NutritionProfile
from app.repositories.nutrition_profile import NutritionProfileRepository
from app.schemas.nutrition_profile import NutritionProfileCreate, NutritionProfileUpdate


class NutritionProfileService:
    """Service for nutrition-profile business logic.

    Encapsulates profile lookup, creation, and update workflows.
    Does not commit, flush, roll back, or close the session.
    """

    def __init__(self, repository: NutritionProfileRepository) -> None:
        self._repository = repository

    async def get_profile(
        self,
        *,
        user_id: uuid.UUID,
    ) -> NutritionProfile:
        """Retrieve the nutrition profile for a given user.

        Raises ``NutritionProfileNotFoundError`` when no profile exists.
        """
        profile = await self._repository.get_by_user_id(user_id)
        if profile is None:
            raise NutritionProfileNotFoundError()
        return profile

    async def create_profile(
        self,
        *,
        user_id: uuid.UUID,
        data: NutritionProfileCreate,
    ) -> NutritionProfile:
        """Create a nutrition profile for the given user.

        Pre-checks for an existing profile to improve normal-operation
        behaviour.  The database unique constraint
        (``uq_nutrition_profiles_user_id``) remains the authoritative
        race-condition protection.

        Raises ``NutritionProfileAlreadyExistsError`` if a profile
        already exists for this user.
        """
        existing = await self._repository.get_by_user_id(user_id)
        if existing is not None:
            raise NutritionProfileAlreadyExistsError()
        profile = await self._repository.create(user_id=user_id, data=data)
        return profile

    async def update_profile(
        self,
        *,
        user_id: uuid.UUID,
        data: NutritionProfileUpdate,
    ) -> NutritionProfile:
        """Update the nutrition profile for a given user.

        Raises ``NutritionProfileNotFoundError`` when no profile exists.
        """
        profile = await self._repository.get_by_user_id(user_id)
        if profile is None:
            raise NutritionProfileNotFoundError()
        profile = await self._repository.update(profile, data)
        return profile
