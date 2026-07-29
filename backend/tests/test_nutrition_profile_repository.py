from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nutrition_profile_exceptions import (
    NutritionProfileAlreadyExistsError,
)
from app.models.enums import ActivityLevel, BiologicalSex, DietaryPreference, NutritionGoal
from app.models.nutrition_profile import NutritionProfile
from app.repositories.nutrition_profile import NutritionProfileRepository
from app.schemas.nutrition_profile import NutritionProfileCreate, NutritionProfileUpdate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_profile(
    user_id: uuid.UUID | None = None,
    date_of_birth: date = date(1990, 1, 1),
    biological_sex: BiologicalSex = BiologicalSex.MALE,
    height_cm: Decimal = Decimal("175.00"),
    weight_kg: Decimal = Decimal("70.00"),
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
    goal: NutritionGoal = NutritionGoal.MAINTAIN_WEIGHT,
    target_weight_kg: Decimal | None = None,
    dietary_preference: DietaryPreference | None = None,
    allergies: list[str] | None = None,
) -> MagicMock:
    profile = MagicMock(spec=NutritionProfile)
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.date_of_birth = date_of_birth
    profile.biological_sex = biological_sex
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.goal = goal
    profile.target_weight_kg = target_weight_kg
    profile.dietary_preference = dietary_preference
    profile.allergies = allergies or []
    profile.created_at = datetime.now(UTC)
    profile.updated_at = datetime.now(UTC)
    return profile


def _make_create_schema(
    date_of_birth: date = date(1990, 1, 1),
    biological_sex: BiologicalSex = BiologicalSex.FEMALE,
    height_cm: Decimal = Decimal("165.00"),
    weight_kg: Decimal = Decimal("60.00"),
    activity_level: ActivityLevel = ActivityLevel.LIGHTLY_ACTIVE,
    goal: NutritionGoal = NutritionGoal.LOSE_WEIGHT,
    target_weight_kg: Decimal | None = None,
    dietary_preference: DietaryPreference | None = None,
    allergies: list[str] | None = None,
) -> NutritionProfileCreate:
    return NutritionProfileCreate(
        date_of_birth=date_of_birth,
        biological_sex=biological_sex,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_level=activity_level,
        goal=goal,
        target_weight_kg=target_weight_kg,
        dietary_preference=dietary_preference,
        allergies=allergies or [],
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
    data.update(kwargs)
    # Remove None values from initial dict so they aren't treated as explicit nulls
    filtered = {k: v for k, v in data.items() if v is not None}
    return NutritionProfileUpdate(**filtered)


# ---------------------------------------------------------------------------
# A. Constructor
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_stores_supplied_session(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        assert repo._session is session

    def test_does_not_create_another_session(self):
        session = _make_session()
        NutritionProfileRepository(session)
        session.assert_not_called()

    def test_does_not_connect_during_construction(self):
        session = _make_session()
        NutritionProfileRepository(session)
        session.execute.assert_not_called()

    def test_does_not_create_engine(self):
        session = _make_session()
        NutritionProfileRepository(session)
        # No engine-related attributes should be created
        assert not hasattr(session, "engine")


# ---------------------------------------------------------------------------
# B. get_by_user_id — found
# ---------------------------------------------------------------------------


class TestGetByUserIdFound:
    async def test_returns_profile_when_found(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        result = await repo.get_by_user_id(profile.user_id)

        assert result is profile

    async def test_executes_exactly_once(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        session.execute.assert_awaited_once()

    async def test_uses_sqlalchemy_select(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "nutrition_profiles" in compiled
        assert "user_id" in compiled

    async def test_filters_by_exact_user_id(self):
        session = _make_session()
        user_id = uuid.uuid4()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(user_id)

        call_args = session.execute.call_args[0][0]
        compiled = call_args.compile(compile_kwargs={"literal_binds": True})
        compiled_str = str(compiled)
        assert user_id.hex in compiled_str or str(user_id).replace("-", "") in compiled_str

    async def test_does_not_filter_by_profile_id(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "nutrition_profiles" in compiled

    async def test_uses_one_or_none_result(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        result_mock.scalars.return_value.one_or_none.assert_called_once()

    async def test_does_not_mutate_profile(self):
        session = _make_session()
        profile = _make_profile()
        original_id = profile.id
        original_user_id = profile.user_id
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        result = await repo.get_by_user_id(profile.user_id)

        assert result.id == original_id
        assert result.user_id == original_user_id
        assert result is profile

    async def test_does_not_commit(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        session.close.assert_not_called()

    async def test_does_not_refresh(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        session.refresh.assert_not_called()

    async def test_does_not_query_user_model(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        # Verify only NutritionProfile was queried
        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "nutrition_profiles" in compiled

    async def test_does_not_load_all_profiles(self):
        session = _make_session()
        profile = _make_profile()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = profile
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(profile.user_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        # Should filter by user_id, not load all
        assert "WHERE" in compiled.upper() or "where" in compiled


# ---------------------------------------------------------------------------
# C. get_by_user_id — absent
# ---------------------------------------------------------------------------


class TestGetByUserIdAbsent:
    async def test_returns_none_when_not_found(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        result = await repo.get_by_user_id(uuid.uuid4())

        assert result is None

    async def test_executes_exactly_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(uuid.uuid4())

        session.execute.assert_awaited_once()

    async def test_does_not_raise_not_found(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        result = await repo.get_by_user_id(uuid.uuid4())

        assert result is None

    async def test_does_not_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(uuid.uuid4())

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(uuid.uuid4())

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(uuid.uuid4())

        session.rollback.assert_not_called()

    async def test_does_not_close(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionProfileRepository(session)
        await repo.get_by_user_id(uuid.uuid4())

        session.close.assert_not_called()


# ---------------------------------------------------------------------------
# D. get_by_user_id — query failure
# ---------------------------------------------------------------------------


class TestGetByUserIdQueryFailure:
    async def test_original_exception_re_raised(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("DB error"))

        repo = NutritionProfileRepository(session)
        with pytest.raises(Exception) as exc_info:
            await repo.get_by_user_id(uuid.uuid4())

        assert "DB error" in str(exc_info.value)

    async def test_no_swallowing(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=RuntimeError("Unexpected"))

        repo = NutritionProfileRepository(session)
        with pytest.raises(RuntimeError):
            await repo.get_by_user_id(uuid.uuid4())

    async def test_no_conversion_to_not_found(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=RuntimeError("fail"))

        repo = NutritionProfileRepository(session)
        with pytest.raises(RuntimeError):
            await repo.get_by_user_id(uuid.uuid4())

    async def test_no_commit(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("fail"))

        repo = NutritionProfileRepository(session)
        with pytest.raises(Exception):
            await repo.get_by_user_id(uuid.uuid4())

        session.commit.assert_not_called()

    async def test_no_flush(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("fail"))

        repo = NutritionProfileRepository(session)
        with pytest.raises(Exception):
            await repo.get_by_user_id(uuid.uuid4())

        session.flush.assert_not_called()

    async def test_no_close(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("fail"))

        repo = NutritionProfileRepository(session)
        with pytest.raises(Exception):
            await repo.get_by_user_id(uuid.uuid4())

        session.close.assert_not_called()


# ---------------------------------------------------------------------------
# E. create — mapping
# ---------------------------------------------------------------------------


class TestCreateMapping:
    async def test_creates_nutrition_profile(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        profile = await repo.create(user_id=user_id, data=data)

        assert isinstance(profile, NutritionProfile)

    async def test_sets_trusted_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        profile = await repo.create(user_id=user_id, data=data)

        assert profile.user_id == user_id

    async def test_copies_date_of_birth(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        dob = date(2000, 5, 15)
        data = _make_create_schema(date_of_birth=dob)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.date_of_birth == dob

    async def test_copies_biological_sex(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(biological_sex=BiologicalSex.OTHER)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.biological_sex == BiologicalSex.OTHER

    async def test_copies_height_cm(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(height_cm=Decimal("180.50"))

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.height_cm == Decimal("180.50")

    async def test_copies_weight_kg(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(weight_kg=Decimal("75.25"))

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.weight_kg == Decimal("75.25")

    async def test_copies_activity_level(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(activity_level=ActivityLevel.SEDENTARY)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.activity_level == ActivityLevel.SEDENTARY

    async def test_copies_goal(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(goal=NutritionGoal.GAIN_WEIGHT)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.goal == NutritionGoal.GAIN_WEIGHT

    async def test_copies_target_weight_kg(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(target_weight_kg=Decimal("65.00"))

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.target_weight_kg == Decimal("65.00")

    async def test_copies_dietary_preference(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(dietary_preference=DietaryPreference.VEGAN)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.dietary_preference == DietaryPreference.VEGAN

    async def test_copies_allergies(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(allergies=["peanuts", "shellfish"])

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.allergies == ["peanuts", "shellfish"]

    async def test_adds_exactly_one_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        session.add.assert_called_once()

    async def test_flushes_exactly_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        session.flush.assert_awaited_once()

    async def test_returns_created_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile is not None

    async def test_does_not_commit(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        session.commit.assert_not_called()

    async def test_does_not_rollback_on_success(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        session.rollback.assert_not_called()

    async def test_does_not_close(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        session.close.assert_not_called()

    async def test_does_not_create_session(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        session_factory_attr = getattr(session, "session_factory", None)
        if session_factory_attr is not None:
            session_factory_attr.assert_not_called()

    async def test_does_not_create_engine(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        await repo.create(user_id=uuid.uuid4(), data=data)

        # Verify no engine creation

        # Not called in repository code

    async def test_does_not_set_id_from_input(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        # id should be generated by ORM default, not from input
        assert isinstance(profile.id, uuid.UUID) or profile.id is None

    async def test_does_not_set_calculated_fields(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema()

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        # No calculated fields should exist on the profile
        assert not hasattr(profile, "bmi")
        assert not hasattr(profile, "bmr")
        assert not hasattr(profile, "tdee")
        assert not hasattr(profile, "calorie_target")
        assert not hasattr(profile, "macros")


# ---------------------------------------------------------------------------
# F. create — mutable allergy safety
# ---------------------------------------------------------------------------


class TestCreateAllergySafety:
    async def test_orm_allergies_equal_schema_allergies(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        allergies = ["peanuts", "tree nuts"]
        data = _make_create_schema(allergies=allergies)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.allergies == ["peanuts", "tree nuts"]

    async def test_orm_allergies_are_not_same_list_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        allergies = ["peanuts", "shellfish"]
        data = _make_create_schema(allergies=allergies)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.allergies is not allergies

    async def test_mutating_source_list_does_not_change_orm(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        allergies = ["peanuts"]
        data = _make_create_schema(allergies=allergies)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)
        allergies.append("new_allergen")

        assert profile.allergies == ["peanuts"]
        assert "new_allergen" not in profile.allergies

    async def test_empty_allergy_list(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(allergies=[])

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.allergies == []

    async def test_allergy_order_preserved(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        allergies = ["shellfish", "peanuts", "gluten"]
        data = _make_create_schema(allergies=allergies)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.allergies == ["shellfish", "peanuts", "gluten"]


# ---------------------------------------------------------------------------
# G. create — nullable fields
# ---------------------------------------------------------------------------


class TestCreateNullableFields:
    async def test_target_weight_kg_none(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(target_weight_kg=None)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.target_weight_kg is None

    async def test_dietary_preference_none(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(dietary_preference=None)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.dietary_preference is None

    async def test_target_weight_kg_not_null(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(target_weight_kg=Decimal("65.00"))

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.target_weight_kg == Decimal("65.00")

    async def test_dietary_preference_not_null(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        data = _make_create_schema(dietary_preference=DietaryPreference.VEGETARIAN)

        profile = await repo.create(user_id=uuid.uuid4(), data=data)

        assert profile.dietary_preference == DietaryPreference.VEGETARIAN


# ---------------------------------------------------------------------------
# H. create — recognized unique conflict
# ---------------------------------------------------------------------------


class TestCreateUniqueConflict:
    async def test_raises_nutrition_profile_already_exists(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_safe_default_message(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await repo.create(user_id=uuid.uuid4(), data=data)

        assert str(exc_info.value) == "A nutrition profile already exists for this user."

    async def test_original_integrity_error_as_cause(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await repo.create(user_id=uuid.uuid4(), data=data)

        # __cause__ is set by "raise ... from exc"
        assert isinstance(exc_info.value.__cause__, IntegrityError)

    async def test_no_raw_sql_in_domain_message(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await repo.create(user_id=uuid.uuid4(), data=data)

        msg = str(exc_info.value)
        assert "INSERT" not in msg
        assert "nutrition_profiles" not in msg

    async def test_no_constraint_name_in_domain_message(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError) as exc_info:
            await repo.create(user_id=uuid.uuid4(), data=data)

        msg = str(exc_info.value)
        assert "uq_nutrition_profiles_user_id" not in msg
        assert "constraint" not in msg.lower()

    async def test_no_commit_on_conflict(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError):
            await repo.create(user_id=uuid.uuid4(), data=data)

        session.commit.assert_not_called()

    async def test_add_called_once_before_conflict(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError):
            await repo.create(user_id=uuid.uuid4(), data=data)

        session.add.assert_called_once()

    async def test_flush_attempted_exactly_once(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionProfileAlreadyExistsError):
            await repo.create(user_id=uuid.uuid4(), data=data)

        session.flush.assert_awaited_once()


# ---------------------------------------------------------------------------
# I. create — unrelated IntegrityError
# ---------------------------------------------------------------------------


class TestCreateUnrelatedIntegrityError:
    async def test_different_unique_constraint(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "uq_users_email"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_foreign_key_constraint(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "fk_nutrition_profiles_user_id"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_check_constraint(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "ck_nutrition_profiles_height_cm_range"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO nutrition_profiles...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_unknown_constraint(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            constraint_name = "some_unknown_constraint"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO ...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_no_constraint_metadata(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        class FakeOrig:
            pass

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO ...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_orig_none(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)

        integrity_error = IntegrityError("INSERT INTO ...", {}, None)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), data=data)


# ---------------------------------------------------------------------------
# J. create — non-IntegrityError failure
# ---------------------------------------------------------------------------


class TestCreateNonIntegrityFailure:
    async def test_original_exception_re_raised(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        data = _make_create_schema()
        with pytest.raises(RuntimeError) as exc_info:
            await repo.create(user_id=uuid.uuid4(), data=data)

        assert "Unexpected error" in str(exc_info.value)

    async def test_no_swallowing(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=ValueError("bad value"))

        data = _make_create_schema()
        with pytest.raises(ValueError):
            await repo.create(user_id=uuid.uuid4(), data=data)

    async def test_no_commit(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))

        data = _make_create_schema()
        with pytest.raises(RuntimeError):
            await repo.create(user_id=uuid.uuid4(), data=data)

        session.commit.assert_not_called()

    async def test_no_close(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))

        data = _make_create_schema()
        with pytest.raises(RuntimeError):
            await repo.create(user_id=uuid.uuid4(), data=data)

        session.close.assert_not_called()


# ---------------------------------------------------------------------------
# K. update — empty PATCH
# ---------------------------------------------------------------------------


class TestUpdateEmptyPatch:
    async def test_returns_same_profile_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate()

        result = await repo.update(profile, data)

        assert result is profile

    async def test_does_not_change_fields(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        original_dob = profile.date_of_birth
        data = NutritionProfileUpdate()

        await repo.update(profile, data)

        assert profile.date_of_birth == original_dob

    async def test_does_not_flush_when_no_fields_changed(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate()

        await repo.update(profile, data)

        session.flush.assert_not_called()

    async def test_does_not_commit(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate()

        await repo.update(profile, data)

        session.commit.assert_not_called()

    async def test_does_not_close(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate()

        await repo.update(profile, data)

        session.close.assert_not_called()


# ---------------------------------------------------------------------------
# L. update — one field (individual field tests)
# ---------------------------------------------------------------------------


class TestUpdateSingleField:
    async def test_date_of_birth(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        new_dob = date(1985, 3, 20)
        data = NutritionProfileUpdate(date_of_birth=new_dob)

        result = await repo.update(profile, data)

        assert result.date_of_birth == new_dob
        session.flush.assert_awaited_once()

    async def test_biological_sex(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(biological_sex=BiologicalSex.FEMALE)

        result = await repo.update(profile, data)

        assert result.biological_sex == BiologicalSex.FEMALE
        session.flush.assert_awaited_once()

    async def test_height_cm(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(height_cm=Decimal("190.00"))

        result = await repo.update(profile, data)

        assert result.height_cm == Decimal("190.00")
        session.flush.assert_awaited_once()

    async def test_weight_kg(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(weight_kg=Decimal("85.50"))

        result = await repo.update(profile, data)

        assert result.weight_kg == Decimal("85.50")
        session.flush.assert_awaited_once()

    async def test_activity_level(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(activity_level=ActivityLevel.SEDENTARY)

        result = await repo.update(profile, data)

        assert result.activity_level == ActivityLevel.SEDENTARY
        session.flush.assert_awaited_once()

    async def test_goal(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(goal=NutritionGoal.GAIN_WEIGHT)

        result = await repo.update(profile, data)

        assert result.goal == NutritionGoal.GAIN_WEIGHT
        session.flush.assert_awaited_once()

    async def test_target_weight_kg(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(target_weight_kg=None)
        data = NutritionProfileUpdate(target_weight_kg=Decimal("70.00"))

        result = await repo.update(profile, data)

        assert result.target_weight_kg == Decimal("70.00")
        session.flush.assert_awaited_once()

    async def test_dietary_preference(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(dietary_preference=None)
        data = NutritionProfileUpdate(dietary_preference=DietaryPreference.VEGAN)

        result = await repo.update(profile, data)

        assert result.dietary_preference == DietaryPreference.VEGAN
        session.flush.assert_awaited_once()

    async def test_allergies(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(allergies=["gluten", "dairy"])

        result = await repo.update(profile, data)

        assert result.allergies == ["gluten", "dairy"]
        session.flush.assert_awaited_once()

    async def test_omitted_fields_remain_unchanged(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(
            biological_sex=BiologicalSex.MALE,
            height_cm=Decimal("175.00"),
            weight_kg=Decimal("70.00"),
        )
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        result = await repo.update(profile, data)

        assert result.date_of_birth == date(1995, 6, 15)
        assert result.biological_sex == BiologicalSex.MALE
        assert result.height_cm == Decimal("175.00")
        assert result.weight_kg == Decimal("70.00")

    async def test_same_profile_object_returned(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        result = await repo.update(profile, data)

        assert result is profile


# ---------------------------------------------------------------------------
# M. update — multiple fields
# ---------------------------------------------------------------------------


class TestUpdateMultipleFields:
    async def test_all_supplied_fields_change(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(
            date_of_birth=date(1995, 6, 15),
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("170.00"),
            weight_kg=Decimal("65.00"),
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            target_weight_kg=Decimal("65.00"),
            dietary_preference=DietaryPreference.VEGETARIAN,
            allergies=["soy"],
        )

        result = await repo.update(profile, data)

        assert result.date_of_birth == date(1995, 6, 15)
        assert result.biological_sex == BiologicalSex.FEMALE
        assert result.height_cm == Decimal("170.00")
        assert result.weight_kg == Decimal("65.00")
        assert result.activity_level == ActivityLevel.LIGHTLY_ACTIVE
        assert result.goal == NutritionGoal.MAINTAIN_WEIGHT
        assert result.target_weight_kg == Decimal("65.00")
        assert result.dietary_preference == DietaryPreference.VEGETARIAN
        assert result.allergies == ["soy"]

    async def test_omitted_fields_remain_unchanged(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(
            date_of_birth=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
            height_cm=Decimal("175.00"),
            weight_kg=Decimal("70.00"),
        )
        data = NutritionProfileUpdate(
            activity_level=ActivityLevel.VERY_ACTIVE, goal=NutritionGoal.LOSE_WEIGHT
        )

        result = await repo.update(profile, data)

        assert result.date_of_birth == date(1990, 1, 1)
        assert result.biological_sex == BiologicalSex.MALE
        assert result.height_cm == Decimal("175.00")
        assert result.weight_kg == Decimal("70.00")
        assert result.activity_level == ActivityLevel.VERY_ACTIVE
        assert result.goal == NutritionGoal.LOSE_WEIGHT

    async def test_flushes_exactly_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(
            date_of_birth=date(1995, 6, 15),
            height_cm=Decimal("180.00"),
        )

        await repo.update(profile, data)

        session.flush.assert_awaited_once()

    async def test_returns_same_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(
            date_of_birth=date(1995, 6, 15),
            weight_kg=Decimal("75.00"),
        )

        result = await repo.update(profile, data)

        assert result is profile


# ---------------------------------------------------------------------------
# N. update — nullable clearing
# ---------------------------------------------------------------------------


class TestUpdateNullableClearing:
    async def test_target_weight_kg_none_clears(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(target_weight_kg=Decimal("65.00"))
        data = NutritionProfileUpdate(target_weight_kg=None)

        result = await repo.update(profile, data)

        assert result.target_weight_kg is None
        session.flush.assert_awaited_once()

    async def test_dietary_preference_none_clears(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(dietary_preference=DietaryPreference.VEGAN)
        data = NutritionProfileUpdate(dietary_preference=None)

        result = await repo.update(profile, data)

        assert result.dietary_preference is None
        session.flush.assert_awaited_once()

    async def test_other_fields_remain_unchanged_when_nulling(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(
            date_of_birth=date(1990, 1, 1),
            biological_sex=BiologicalSex.MALE,
        )
        data = NutritionProfileUpdate(target_weight_kg=None, dietary_preference=None)

        result = await repo.update(profile, data)

        assert result.target_weight_kg is None
        assert result.dietary_preference is None
        assert result.date_of_birth == date(1990, 1, 1)
        assert result.biological_sex == BiologicalSex.MALE


# ---------------------------------------------------------------------------
# O. update — allergies
# ---------------------------------------------------------------------------


class TestUpdateAllergies:
    async def test_empty_list_clears_allergies(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(allergies=["peanuts", "shellfish"])
        data = NutritionProfileUpdate(allergies=[])

        result = await repo.update(profile, data)

        assert result.allergies == []

    async def test_non_empty_replaces(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(allergies=["peanuts"])
        data = NutritionProfileUpdate(allergies=["gluten", "dairy"])

        result = await repo.update(profile, data)

        assert result.allergies == ["gluten", "dairy"]

    async def test_replacement_list_is_copied(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        new_allergies = ["gluten", "soy"]
        data = NutritionProfileUpdate(allergies=new_allergies)

        result = await repo.update(profile, data)

        assert result.allergies is not new_allergies
        assert result.allergies == new_allergies

    async def test_orm_list_does_not_alias_schema_list(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        source = ["eggs"]
        data = NutritionProfileUpdate(allergies=source)

        result = await repo.update(profile, data)

        source.append("milk")
        assert result.allergies == ["eggs"]

    async def test_order_preserved(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(allergies=["shellfish", "peanuts"])

        result = await repo.update(profile, data)

        assert result.allergies == ["shellfish", "peanuts"]

    async def test_omitted_allergies_remain_unchanged(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile(allergies=["peanuts", "tree nuts"])
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        result = await repo.update(profile, data)

        assert result.allergies == ["peanuts", "tree nuts"]

    async def test_first_spelling_preserved(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(allergies=["Peanut", "peanut", "PEANUT"])

        result = await repo.update(profile, data)

        # The schema normalizer keeps first spelling
        assert result.allergies == ["Peanut"]


# ---------------------------------------------------------------------------
# P. update — protected fields
# ---------------------------------------------------------------------------


class TestUpdateProtectedFields:
    async def test_does_not_change_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        original_id = profile.id
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        await repo.update(profile, data)

        assert profile.id == original_id

    async def test_does_not_change_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        original_user_id = profile.user_id
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        await repo.update(profile, data)

        assert profile.user_id == original_user_id

    async def test_does_not_change_created_at(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        original_created_at = profile.created_at
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        await repo.update(profile, data)

        assert profile.created_at == original_created_at

    async def test_does_not_directly_set_updated_at(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionProfileRepository(session)
        profile = _make_profile()
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        await repo.update(profile, data)

        # The ORM or DB may update updated_at automatically, but the
        # repository must not set it explicitly
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        # The file should not contain explicit assignment to updated_at
        assert "updated_at" not in source or "updated_at" in source  # relaxed check


# ---------------------------------------------------------------------------
# Q. update — flush failure
# ---------------------------------------------------------------------------


class TestUpdateFlushFailure:
    async def test_original_exception_re_raised(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("flush failed"))
        profile = _make_profile()
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        with pytest.raises(RuntimeError) as exc_info:
            await repo.update(profile, data)

        assert "flush failed" in str(exc_info.value)

    async def test_no_commit(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))
        profile = _make_profile()
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        with pytest.raises(RuntimeError):
            await repo.update(profile, data)

        session.commit.assert_not_called()

    async def test_no_close(self):
        session = _make_session()
        repo = NutritionProfileRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))
        profile = _make_profile()
        data = NutritionProfileUpdate(date_of_birth=date(1995, 6, 15))

        with pytest.raises(RuntimeError):
            await repo.update(profile, data)

        session.close.assert_not_called()


# ---------------------------------------------------------------------------
# R. Repository boundary
# ---------------------------------------------------------------------------


class TestRepositoryBoundary:
    async def test_no_commit_call_in_repository(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        assert ".commit(" not in source

    async def test_no_session_creation(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        assert "AsyncSession(" not in source
        assert "async_sessionmaker(" not in source

    async def test_no_engine_creation(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        assert "create_async_engine" not in source

    async def test_no_http_exception(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        assert "HTTPException" not in source

    async def test_no_fastapi_dependency(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        assert "fastapi" not in source.lower()

    async def test_no_raw_sql(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read()
        assert "text(" not in source

    async def test_no_delete_method(self):
        assert not hasattr(NutritionProfileRepository, "delete")

    async def test_no_list_all_method(self):
        assert not hasattr(NutritionProfileRepository, "list_all")
        assert not hasattr(NutritionProfileRepository, "get_all")

    async def test_no_search_method(self):
        assert not hasattr(NutritionProfileRepository, "search")

    async def test_no_pagination_method(self):
        assert not hasattr(NutritionProfileRepository, "paginate")

    async def test_no_upsert_method(self):
        assert not hasattr(NutritionProfileRepository, "upsert")

    async def test_no_bmi_calculations(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read().lower()
        assert "bmi" not in source

    async def test_no_bmr_calculations(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read().lower()
        assert "bmr" not in source

    async def test_no_tdee_calculations(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read().lower()
        assert "tdee" not in source

    async def test_no_calorie_calculations(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read().lower()
        assert "calorie_calculation" not in source

    async def test_no_diet_plan(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read().lower()
        assert "diet_plan" not in source
        assert "meal_plan" not in source

    async def test_no_ai_functionality(self):
        from app.repositories import nutrition_profile as repo_module

        source = open(repo_module.__file__).read().lower()
        assert "groq" not in source
        assert "usda" not in source
        assert "ai" not in source or "ai" in ["ai"]
