from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.nutrition_profile_exceptions import (
    NutritionProfileAlreadyExistsError,
    NutritionProfileNotFoundError,
)
from app.models.enums import ActivityLevel, BiologicalSex, DietaryPreference, NutritionGoal
from app.models.nutrition_profile import NutritionProfile
from app.repositories.nutrition_profile import NutritionProfileRepository
from app.schemas.nutrition_profile import NutritionProfileCreate, NutritionProfileUpdate
from app.services.nutrition_profile import NutritionProfileService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo() -> MagicMock:
    return AsyncMock(spec=NutritionProfileRepository)


def _make_profile() -> MagicMock:
    profile = MagicMock(spec=NutritionProfile)
    profile.id = uuid.uuid4()
    profile.user_id = uuid.uuid4()
    profile.date_of_birth = date(1990, 1, 1)
    profile.biological_sex = BiologicalSex.MALE
    profile.height_cm = Decimal("175.00")
    profile.weight_kg = Decimal("70.00")
    profile.activity_level = ActivityLevel.MODERATELY_ACTIVE
    profile.goal = NutritionGoal.MAINTAIN_WEIGHT
    profile.target_weight_kg = None
    profile.dietary_preference = None
    profile.allergies = []
    profile.full_name = None
    profile.phone = None
    profile.avatar_url = None
    profile.fitness_goal = None
    profile.medical_conditions = []
    profile.water_goal_ml = None
    profile.sleep_goal_hours = None
    profile.daily_calorie_goal = None
    profile.daily_protein_goal_g = None
    profile.daily_carb_goal_g = None
    profile.daily_fat_goal_g = None
    return profile


def _make_create_schema() -> NutritionProfileCreate:
    return NutritionProfileCreate(
        date_of_birth=date(1990, 1, 1),
        biological_sex=BiologicalSex.FEMALE,
        height_cm=Decimal("165.00"),
        weight_kg=Decimal("60.00"),
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        goal=NutritionGoal.LOSE_WEIGHT,
        target_weight_kg=Decimal("55.00"),
        dietary_preference=DietaryPreference.VEGAN,
        allergies=["peanuts"],
    )


def _make_update_schema(**kwargs) -> NutritionProfileUpdate:
    data = {
        "date_of_birth": date(1995, 6, 15),
        "biological_sex": BiologicalSex.MALE,
        "height_cm": Decimal("180.00"),
        "weight_kg": Decimal("80.00"),
        "activity_level": ActivityLevel.VERY_ACTIVE,
        "goal": NutritionGoal.GAIN_MUSCLE,
    }
    data.update({k: v for k, v in kwargs.items() if v is not None})
    return NutritionProfileUpdate(**data)


# ---------------------------------------------------------------------------
# A. Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_accepts_repository(self):
        repo = _make_repo()
        service = NutritionProfileService(repo)
        assert service._repository is repo

    def test_stores_exact_repository(self):
        repo = _make_repo()
        service = NutritionProfileService(repo)
        assert service._repository is repo

    def test_does_not_create_repository(self):
        repo = _make_repo()
        NutritionProfileService(repo)
        repo.assert_not_called()

    def test_does_not_query_during_construction(self):
        repo = _make_repo()
        NutritionProfileService(repo)
        repo.get_by_user_id.assert_not_called()
        repo.create.assert_not_called()
        repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# B. get_profile — found
# ---------------------------------------------------------------------------


class TestGetProfileFound:
    async def test_calls_get_by_user_id_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        await service.get_profile(user_id=user_id)

        repo.get_by_user_id.assert_awaited_once()

    async def test_passes_exact_user_id(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        await service.get_profile(user_id=user_id)

        repo.get_by_user_id.assert_awaited_once_with(user_id)

    async def test_returns_exact_profile(self):
        repo = _make_repo()
        expected_profile = _make_profile()
        repo.get_by_user_id.return_value = expected_profile
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        result = await service.get_profile(user_id=user_id)

        assert result is expected_profile

    async def test_does_not_call_create(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        await service.get_profile(user_id=user_id)

        repo.create.assert_not_called()

    async def test_does_not_call_update(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        await service.get_profile(user_id=user_id)

        repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# C. get_profile — absent
# ---------------------------------------------------------------------------


class TestGetProfileAbsent:
    async def test_raises_nutrition_profile_not_found(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.get_profile(user_id=user_id)

    async def test_safe_exact_message(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(NutritionProfileNotFoundError) as exc_info:
            await service.get_profile(user_id=user_id)

        assert str(exc_info.value) == "Nutrition profile not found."

    async def test_calls_get_by_user_id_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.get_profile(user_id=user_id)

        repo.get_by_user_id.assert_awaited_once()

    async def test_does_not_call_create(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.get_profile(user_id=user_id)

        repo.create.assert_not_called()

    async def test_does_not_call_update(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.get_profile(user_id=user_id)

        repo.update.assert_not_called()

    async def test_does_not_return_none(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.get_profile(user_id=user_id)


# ---------------------------------------------------------------------------
# D. get_profile — repository failure
# ---------------------------------------------------------------------------


class TestGetProfileRepoFailure:
    async def test_original_exception_re_raised(self):
        repo = _make_repo()
        repo.get_by_user_id.side_effect = RuntimeError("DB error")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(RuntimeError) as exc_info:
            await service.get_profile(user_id=user_id)

        assert "DB error" in str(exc_info.value)

    async def test_no_swallowing(self):
        repo = _make_repo()
        repo.get_by_user_id.side_effect = ValueError("unexpected")
        service = NutritionProfileService(repo)

        with pytest.raises(ValueError):
            await service.get_profile(user_id=uuid.uuid4())

    async def test_no_conversion_to_not_found(self):
        repo = _make_repo()
        repo.get_by_user_id.side_effect = RuntimeError("fail")
        service = NutritionProfileService(repo)

        with pytest.raises(RuntimeError):
            await service.get_profile(user_id=uuid.uuid4())


# ---------------------------------------------------------------------------
# E. create_profile — no existing profile
# ---------------------------------------------------------------------------


class TestCreateProfileNoExisting:
    async def test_calls_get_by_user_id_first(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_profile(user_id=user_id, data=data)

        repo.get_by_user_id.assert_awaited_once()

    async def test_passes_exact_user_id_to_get(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_profile(user_id=user_id, data=data)

        repo.get_by_user_id.assert_awaited_once_with(user_id)

    async def test_calls_create_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_awaited_once()

    async def test_passes_exact_user_id_to_create(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_awaited_once_with(user_id=user_id, data=data)

    async def test_passes_exact_schema_object(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_profile(user_id=user_id, data=data)

        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["data"] is data

    async def test_returns_exact_created_profile(self):
        repo = _make_repo()
        expected_profile = _make_profile()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = expected_profile
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        result = await service.create_profile(user_id=user_id, data=data)

        assert result is expected_profile

    async def test_call_order_get_then_create(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        call_order = []
        repo.get_by_user_id = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("get") or None
        )
        repo.create = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("create") or _make_profile()
        )

        await service.create_profile(user_id=user_id, data=data)

        assert call_order == ["get", "create"]

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_does_not_mutate_schema(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()
        original_allergies = list(data.allergies)

        await service.create_profile(user_id=user_id, data=data)

        assert data.allergies == original_allergies

    async def test_does_not_calculate_values(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        result = await service.create_profile(user_id=user_id, data=data)

        assert not hasattr(result, "bmi")
        assert not hasattr(result, "bmi_category")
        assert not hasattr(result, "bmr")
        assert not hasattr(result, "tdee")
        assert not hasattr(result, "calorie_target")
        assert not hasattr(result, "macros")


# ---------------------------------------------------------------------------
# F. create_profile — existing profile
# ---------------------------------------------------------------------------


class TestCreateProfileExisting:
    async def test_raises_nutrition_profile_already_exists(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

    async def test_safe_exact_message(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await service.create_profile(user_id=user_id, data=data)

        assert str(exc_info.value) == "A nutrition profile already exists for this user."

    async def test_calls_get_by_user_id_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

        repo.get_by_user_id.assert_awaited_once()

    async def test_does_not_call_create(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_not_called()

    async def test_does_not_modify_existing_profile(self):
        repo = _make_repo()
        existing = _make_profile()
        existing_date_of_birth = existing.date_of_birth
        repo.get_by_user_id.return_value = existing
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

        assert existing.date_of_birth == existing_date_of_birth

    async def test_does_not_expose_user_id(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await service.create_profile(user_id=user_id, data=data)

        assert str(user_id) not in str(exc_info.value)

    async def test_does_not_expose_database_details(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await service.create_profile(user_id=user_id, data=data)

        msg = str(exc_info.value)
        assert "IntegrityError" not in msg
        assert "constraint" not in msg.lower()


# ---------------------------------------------------------------------------
# G. create_profile — race-condition conflict
# ---------------------------------------------------------------------------


class TestCreateProfileRace:
    async def test_repository_create_raises_already_exists(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = NutritionProfileAlreadyExistsError()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

    async def test_safe_message_preserved(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = NutritionProfileAlreadyExistsError()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await service.create_profile(user_id=user_id, data=data)

        assert "already exists" in str(exc_info.value)

    async def test_no_second_create_attempt(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = NutritionProfileAlreadyExistsError()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_awaited_once()

    async def test_no_retry_loop(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = NutritionProfileAlreadyExistsError()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionProfileAlreadyExistsError):
            await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_awaited_once()


# ---------------------------------------------------------------------------
# H. create_profile — repository query failure
# ---------------------------------------------------------------------------


class TestCreateProfileQueryFailure:
    async def test_original_exception_re_raised(self):
        repo = _make_repo()
        repo.get_by_user_id.side_effect = RuntimeError("query failed")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(RuntimeError):
            await service.create_profile(user_id=user_id, data=data)

    async def test_create_not_called(self):
        repo = _make_repo()
        repo.get_by_user_id.side_effect = RuntimeError("fail")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(RuntimeError):
            await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# I. create_profile — repository create failure
# ---------------------------------------------------------------------------


class TestCreateProfileCreateFailure:
    async def test_original_exception_re_raised(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = RuntimeError("create failed")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(RuntimeError):
            await service.create_profile(user_id=user_id, data=data)

    async def test_no_swallowing(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = ValueError("bad data")
        service = NutritionProfileService(repo)

        with pytest.raises(ValueError):
            await service.create_profile(user_id=uuid.uuid4(), data=_make_create_schema())

    async def test_no_retry(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = RuntimeError("fail")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(RuntimeError):
            await service.create_profile(user_id=user_id, data=data)

        repo.create.assert_awaited_once()


# ---------------------------------------------------------------------------
# J. update_profile — found
# ---------------------------------------------------------------------------


class TestUpdateProfileFound:
    async def test_calls_get_by_user_id_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        await service.update_profile(user_id=user_id, data=data)

        repo.get_by_user_id.assert_awaited_once()

    async def test_passes_exact_user_id_to_get(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        await service.update_profile(user_id=user_id, data=data)

        repo.get_by_user_id.assert_awaited_once_with(user_id)

    async def test_calls_update_exactly_once(self):
        repo = _make_repo()
        expected_profile = _make_profile()
        repo.get_by_user_id.return_value = expected_profile
        repo.update.return_value = expected_profile
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        await service.update_profile(user_id=user_id, data=data)

        repo.update.assert_awaited_once()

    async def test_passes_exact_profile_to_update(self):
        repo = _make_repo()
        expected_profile = _make_profile()
        repo.get_by_user_id.return_value = expected_profile
        repo.update.return_value = expected_profile
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        await service.update_profile(user_id=user_id, data=data)

        call_args = repo.update.call_args
        assert call_args[0][0] is expected_profile

    async def test_passes_exact_schema_to_update(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        await service.update_profile(user_id=user_id, data=data)

        call_args = repo.update.call_args[0]
        assert call_args[1] is data

    async def test_returns_exact_updated_profile(self):
        repo = _make_repo()
        existing = _make_profile()
        updated = _make_profile()
        repo.get_by_user_id.return_value = existing
        repo.update.return_value = updated
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        result = await service.update_profile(user_id=user_id, data=data)

        assert result is updated

    async def test_call_order_get_then_update(self):
        repo = _make_repo()
        profile = _make_profile()
        call_order = []
        repo.get_by_user_id = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("get") or profile
        )
        repo.update = AsyncMock(side_effect=lambda *a, **kw: call_order.append("update") or profile)

        service = NutritionProfileService(repo)
        data = _make_update_schema()

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        assert call_order == ["get", "update"]

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.return_value = _make_profile()
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        await service.update_profile(user_id=user_id, data=data)

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_calculate_values(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = _make_update_schema()

        result = await service.update_profile(user_id=uuid.uuid4(), data=data)

        assert not hasattr(result, "bmi")
        assert not hasattr(result, "bmi_category")
        assert not hasattr(result, "bmr")
        assert not hasattr(result, "tdee")
        assert not hasattr(result, "calorie_target")
        assert not hasattr(result, "macros")


# ---------------------------------------------------------------------------
# K. update_profile — absent
# ---------------------------------------------------------------------------


class TestUpdateProfileAbsent:
    async def test_raises_nutrition_profile_not_found(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.update_profile(user_id=user_id, data=data)

    async def test_safe_exact_message(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(NutritionProfileNotFoundError) as exc_info:
            await service.update_profile(user_id=user_id, data=data)

        assert str(exc_info.value) == "Nutrition profile not found."

    async def test_calls_get_by_user_id_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.update_profile(user_id=user_id, data=data)

        repo.get_by_user_id.assert_awaited_once()

    async def test_does_not_call_update(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.update_profile(user_id=user_id, data=data)

        repo.update.assert_not_called()

    async def test_does_not_create_profile_automatically(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.update_profile(user_id=user_id, data=data)

        repo.create.assert_not_called()

    async def test_does_not_upsert(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = None
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(NutritionProfileNotFoundError):
            await service.update_profile(user_id=user_id, data=data)

        # No update should be called either
        repo.update.assert_not_called()


# ---------------------------------------------------------------------------
# L. update_profile — empty PATCH
# ---------------------------------------------------------------------------


class TestUpdateProfileEmpty:
    async def test_calls_repository_update_with_empty_schema(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate()

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        repo.update.assert_awaited_once()

    async def test_does_not_infer_fields(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate()

        result = await service.update_profile(user_id=uuid.uuid4(), data=data)

        # No fields should be inferred or changed
        assert result is profile

    async def test_does_not_create_defaults(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate()

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        # No default values should be added
        repo.update.assert_awaited_once_with(profile, data)


# ---------------------------------------------------------------------------
# M. update_profile — nullable clearing
# ---------------------------------------------------------------------------


class TestUpdateProfileNullable:
    async def test_target_weight_kg_none_passed_unchanged(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate(target_weight_kg=None)

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        repo.update.assert_awaited_once_with(profile, data)

    async def test_dietary_preference_none_passed_unchanged(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate(dietary_preference=None)

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        repo.update.assert_awaited_once_with(profile, data)

    async def test_no_inference_for_nullable_fields(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate(target_weight_kg=None, dietary_preference=None)

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        repo.update.assert_awaited_once_with(profile, data)


# ---------------------------------------------------------------------------
# N. update_profile — allergy clearing
# ---------------------------------------------------------------------------


class TestUpdateProfileAllergies:
    async def test_empty_allergies_passed_unchanged(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate(allergies=[])

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        repo.update.assert_awaited_once_with(profile, data)

    async def test_no_default_allergies_added(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate(allergies=[])

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        call_args = repo.update.call_args[0]
        assert call_args[1].allergies == []

    async def test_no_inferred_allergies(self):
        repo = _make_repo()
        profile = _make_profile()
        repo.get_by_user_id.return_value = profile
        repo.update.return_value = profile
        service = NutritionProfileService(repo)
        data = NutritionProfileUpdate()

        await service.update_profile(user_id=uuid.uuid4(), data=data)

        call_args = repo.update.call_args[0]
        # allergies should not be set if not in model_fields_set
        assert "allergies" not in call_args[1].model_fields_set


# ---------------------------------------------------------------------------
# O. update_profile — repository failure
# ---------------------------------------------------------------------------


class TestUpdateProfileRepoFailure:
    async def test_original_exception_re_raised(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.side_effect = RuntimeError("update failed")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(RuntimeError) as exc_info:
            await service.update_profile(user_id=user_id, data=data)

        assert "update failed" in str(exc_info.value)

    async def test_no_swallowing(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.side_effect = ValueError("bad update")
        service = NutritionProfileService(repo)

        with pytest.raises(ValueError):
            await service.update_profile(user_id=uuid.uuid4(), data=_make_update_schema())

    async def test_no_retry(self):
        repo = _make_repo()
        repo.get_by_user_id.return_value = _make_profile()
        repo.update.side_effect = RuntimeError("fail")
        service = NutritionProfileService(repo)
        user_id = uuid.uuid4()
        data = _make_update_schema()

        with pytest.raises(RuntimeError):
            await service.update_profile(user_id=user_id, data=data)

        repo.update.assert_awaited_once()


# ---------------------------------------------------------------------------
# P. Service boundary
# ---------------------------------------------------------------------------


class TestServiceBoundary:
    def test_no_async_session_dependency(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "AsyncSession" not in source

    def test_no_sqlalchemy_import(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_fastapi_import(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "HTTPException" not in source

    def test_no_direct_select(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "select(" not in source

    def test_no_direct_sql(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "text(" not in source

    def test_no_commit(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert ".commit(" not in source

    def test_no_flush(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert ".flush(" not in source

    def test_no_rollback(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert ".rollback(" not in source

    def test_no_close(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert ".close(" not in source

    def test_no_repository_construction_internally(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "NutritionProfileRepository(" not in source

    def test_no_database_configuration(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read()
        assert "DATABASE_URL" not in source
        assert "settings" not in source

    def test_no_bmi_calculations(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "bmi" not in source

    def test_no_bmr_calculations(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "bmr" not in source

    def test_no_tdee_calculations(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "tdee" not in source

    def test_no_calorie_target(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "calorie" not in source

    def test_no_macros(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "macros" not in source

    def test_no_recommendation(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "recommend" not in source

    def test_no_diet_plan(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "diet_plan" not in source
        assert "meal_plan" not in source

    def test_no_ai_functionality(self):
        from app.services import nutrition_profile as service_module

        source = open(service_module.__file__).read().lower()
        assert "groq" not in source
        assert "usda" not in source


# ---------------------------------------------------------------------------
# Q. Import side effects
# ---------------------------------------------------------------------------


class TestServiceImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        from app.services import NutritionProfileService

        assert NutritionProfileService is not None

    def test_import_does_not_require_postgres(self):
        from app.services.nutrition_profile import NutritionProfileService

        assert NutritionProfileService is not None

    def test_import_works_without_database_url(self):
        from app.services import NutritionProfileService

        assert NutritionProfileService is not None
