from __future__ import annotations

import copy
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nutrition_profile_exceptions import (
    NutritionProfileAlreadyExistsError,
)
from app.models.nutrition_profile import NutritionProfile
from app.schemas.nutrition_profile import NutritionProfileCreate, NutritionProfileUpdate


def _is_unique_constraint_violation(
    exc: IntegrityError,
    constraint_name: str,
) -> bool:
    """Check if an IntegrityError is caused by a specific named constraint."""
    orig = exc.orig
    if orig is None:
        return False
    if hasattr(orig, "constraint_name"):
        return orig.constraint_name == constraint_name
    return constraint_name in str(orig)


_APPROVED_CREATE_FIELDS = (
    "date_of_birth",
    "biological_sex",
    "height_cm",
    "weight_kg",
    "activity_level",
    "goal",
    "target_weight_kg",
    "dietary_preference",
    "allergies",
    "full_name",
    "phone",
    "avatar_url",
    "fitness_goal",
    "medical_conditions",
    "water_goal_ml",
    "sleep_goal_hours",
    "daily_calorie_goal",
    "daily_protein_goal_g",
    "daily_carb_goal_g",
    "daily_fat_goal_g",
)


class NutritionProfileRepository:
    """Repository for NutritionProfile database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> NutritionProfile | None:
        """Look up a nutrition profile by user_id.

        Returns the NutritionProfile when found, or None when not found.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = select(NutritionProfile).where(NutritionProfile.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        data: NutritionProfileCreate,
    ) -> NutritionProfile:
        """Create and persist a new nutrition profile.

        Accepts a trusted user_id and a validated NutritionProfileCreate schema.
        Adds the NutritionProfile to the session and flushes.
        The caller owns transaction commit/rollback.

        Raises ``NutritionProfileAlreadyExistsError`` on duplicate user_id.
        """
        allergies = copy.copy(data.allergies) if data.allergies is not None else []
        profile = NutritionProfile(
            user_id=user_id,
            date_of_birth=data.date_of_birth,
            biological_sex=data.biological_sex,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            activity_level=data.activity_level,
            goal=data.goal,
            target_weight_kg=data.target_weight_kg,
            dietary_preference=data.dietary_preference,
            allergies=allergies,
            full_name=data.full_name,
            phone=data.phone,
            avatar_url=data.avatar_url,
            fitness_goal=data.fitness_goal,
            medical_conditions=copy.copy(data.medical_conditions) if data.medical_conditions is not None else [],
            water_goal_ml=data.water_goal_ml,
            sleep_goal_hours=data.sleep_goal_hours,
            daily_calorie_goal=data.daily_calorie_goal,
            daily_protein_goal_g=data.daily_protein_goal_g,
            daily_carb_goal_g=data.daily_carb_goal_g,
            daily_fat_goal_g=data.daily_fat_goal_g,
        )
        self._session.add(profile)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if _is_unique_constraint_violation(exc, "uq_nutrition_profiles_user_id"):
                raise NutritionProfileAlreadyExistsError() from exc
            raise
        return profile

    async def update(
        self,
        profile: NutritionProfile,
        data: NutritionProfileUpdate,
    ) -> NutritionProfile:
        """Update an existing nutrition profile using PATCH semantics.

        Only fields explicitly supplied in the PATCH schema are updated.
        Omitted fields remain unchanged.
        The caller owns transaction commit/rollback.
        """
        for field in data.model_fields_set:
            if field == "allergies":
                value = data.allergies
                if value is not None:
                    profile.allergies = list(value)
                else:
                    profile.allergies = None
            elif field == "target_weight_kg":
                profile.target_weight_kg = data.target_weight_kg
            elif field == "dietary_preference":
                profile.dietary_preference = data.dietary_preference
            else:
                setattr(profile, field, getattr(data, field))
        if data.model_fields_set:
            await self._session.flush()
        return profile
