from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nutrition_log_exceptions import (
    NutritionLogEntryAlreadyExistsError,
)
from app.core.nutrition_logs import MealType
from app.models.nutrition_log import NutritionLog
from app.repositories.nutrition_log import NutritionLogRepository
from app.schemas.nutrition_logs import NutritionLogEntryCreate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_entry(
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date = date(2025, 1, 1),
    food_name: str = "Oatmeal",
    meal_type: MealType = MealType.BREAKFAST,
    serving_description: str = "1 bowl",
    calories_kcal: Decimal = Decimal("300.00"),
    protein_g: Decimal = Decimal("10.00"),
    carbohydrate_g: Decimal = Decimal("50.00"),
    fat_g: Decimal = Decimal("5.00"),
) -> MagicMock:
    entry = MagicMock(spec=NutritionLog)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.entry_id = entry_id or uuid.uuid4()
    entry.logged_date = logged_date
    entry.food_name = food_name
    entry.meal_type = meal_type
    entry.serving_description = serving_description
    entry.calories_kcal = calories_kcal
    entry.protein_g = protein_g
    entry.carbohydrate_g = carbohydrate_g
    entry.fat_g = fat_g
    return entry


def _make_create_schema(
    entry_id: uuid.UUID | None = None,
    food_name: str = "Oatmeal",
    meal_type: MealType = MealType.BREAKFAST,
    serving_description: str = "1 bowl",
    calories_kcal: Decimal = Decimal("300"),
    protein_g: Decimal = Decimal("10"),
    carbohydrate_g: Decimal = Decimal("50"),
    fat_g: Decimal = Decimal("5"),
) -> NutritionLogEntryCreate:
    return NutritionLogEntryCreate(
        entry_id=entry_id or uuid.uuid4(),
        food_name=food_name,
        meal_type=meal_type,
        serving_description=serving_description,
        calories_kcal=calories_kcal,
        protein_g=protein_g,
        carbohydrate_g=carbohydrate_g,
        fat_g=fat_g,
    )


# ===========================================================================
# A. Constructor
# ===========================================================================


class TestConstructor:
    def test_stores_supplied_session(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        assert repo._session is session

    def test_does_not_create_another_session(self):
        session = _make_session()
        NutritionLogRepository(session)
        session.assert_not_called()

    def test_does_not_connect_during_construction(self):
        session = _make_session()
        NutritionLogRepository(session)
        session.execute.assert_not_called()

    def test_does_not_create_engine(self):
        session = _make_session()
        NutritionLogRepository(session)
        assert not hasattr(session, "engine")


# ===========================================================================
# B. list_by_user_and_date — general
# ===========================================================================


class TestListByUserAndDateGeneral:
    async def test_uses_select_nutrition_log(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "nutrition_logs" in compiled

    async def test_filters_by_user_id(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        await repo.list_by_user_and_date(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert user_id.hex in compiled.replace("-", "")

    async def test_filters_by_logged_date(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        target_date = date(2025, 6, 15)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=target_date,
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "2025-06-15" in compiled

    async def test_uses_both_filters(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        target_date = date(2025, 3, 10)
        await repo.list_by_user_and_date(
            user_id=user_id,
            logged_date=target_date,
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "WHERE" in compiled.upper() or "where" in compiled

    async def test_does_not_filter_by_user_id_alone(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        target_date = date(2025, 1, 1)
        await repo.list_by_user_and_date(
            user_id=user_id,
            logged_date=target_date,
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "logged_date" in compiled

    async def test_does_not_filter_by_date_alone(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        await repo.list_by_user_and_date(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled

    async def test_executes_exactly_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        session.execute.assert_awaited_once()

    async def test_returns_list(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        assert isinstance(result, list)

    async def test_returns_new_list(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result1 = await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )
        result2 = await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        assert result1 is not result2

    async def test_returns_empty_list_when_no_rows(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        assert result == []

    async def test_returns_all_matching_rows(self):
        session = _make_session()
        entry1 = _make_entry()
        entry2 = _make_entry()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [entry1, entry2]
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        assert len(result) == 2
        assert result[0] is entry1
        assert result[1] is entry2

    async def test_does_not_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        session.close.assert_not_called()

    async def test_does_not_refresh(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        session.refresh.assert_not_called()


class TestListByUserAndDateOrdering:
    async def test_meal_order_breakfast_first(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))

        expected_case = "CASE"
        assert expected_case in compiled.upper()

    async def test_preserves_deterministic_database_ordering(self):
        session = _make_session()
        entry_a = _make_entry()
        entry_b = _make_entry()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [entry_a, entry_b]
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.list_by_user_and_date(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
        )

        assert result == [entry_a, entry_b]

    async def test_re_raises_unexpected_execution_exceptions(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("DB error"))

        repo = NutritionLogRepository(session)
        with pytest.raises(Exception) as exc_info:
            await repo.list_by_user_and_date(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
            )

        assert "DB error" in str(exc_info.value)


# ===========================================================================
# C. get_by_user_and_entry_id
# ===========================================================================


class TestGetByUserAndEntryId:
    async def test_filters_by_both_user_id_and_entry_id(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()
        await repo.get_by_user_and_entry_id(
            user_id=user_id,
            entry_id=entry_id,
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled
        assert "entry_id" in compiled

    async def test_returns_matching_object(self):
        session = _make_session()
        entry = _make_entry()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = entry
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.get_by_user_and_entry_id(
            user_id=entry.user_id,
            entry_id=entry.entry_id,
        )

        assert result is entry

    async def test_returns_none_when_absent(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        assert result is None

    async def test_uses_one_or_none_semantics(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        result_mock.scalars.return_value.one_or_none.assert_called_once()

    async def test_executes_exactly_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        session.execute.assert_awaited_once()

    async def test_does_not_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        session.close.assert_not_called()

    async def test_does_not_refresh(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
        )

        session.refresh.assert_not_called()

    async def test_does_not_mutate(self):
        session = _make_session()
        entry = _make_entry()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = entry
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        result = await repo.get_by_user_and_entry_id(
            user_id=entry.user_id,
            entry_id=entry.entry_id,
        )

        assert result.user_id == entry.user_id
        assert result.entry_id == entry.entry_id
        assert result is entry

    async def test_re_raises_unexpected_execution_errors(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("query failed"))

        repo = NutritionLogRepository(session)
        with pytest.raises(Exception) as exc_info:
            await repo.get_by_user_and_entry_id(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
            )

        assert "query failed" in str(exc_info.value)

    async def test_never_queries_by_entry_id_alone(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = NutritionLogRepository(session)
        entry_id = uuid.uuid4()
        await repo.get_by_user_and_entry_id(
            user_id=uuid.uuid4(),
            entry_id=entry_id,
        )

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled


# ===========================================================================
# D. create — mapping
# ===========================================================================


class TestCreateMapping:
    async def test_creates_nutrition_log(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        entry = await repo.create(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert isinstance(entry, NutritionLog)

    async def test_sets_trusted_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        entry = await repo.create(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.user_id == user_id

    async def test_does_not_allow_schema_data_to_override_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        entry = await repo.create(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.user_id == user_id
        assert not hasattr(data, "user_id")

    async def test_maps_caller_owned_entry_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry_id = uuid.uuid4()
        data = _make_create_schema(entry_id=entry_id)

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.entry_id == entry_id

    async def test_maps_logged_date(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        target_date = date(2025, 7, 4)
        data = _make_create_schema()

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=target_date,
            data=data,
        )

        assert entry.logged_date == target_date

    async def test_maps_food_name(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(food_name="Chicken Salad")

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.food_name == "Chicken Salad"

    async def test_maps_meal_type(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(meal_type=MealType.LUNCH)

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.meal_type is MealType.LUNCH

    async def test_maps_serving_description(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(serving_description="2 cups")

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.serving_description == "2 cups"

    async def test_maps_calories(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(calories_kcal=Decimal("500"))

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.calories_kcal == Decimal("500")

    async def test_maps_protein(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(protein_g=Decimal("25"))

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.protein_g == Decimal("25")

    async def test_maps_carbohydrate(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(carbohydrate_g=Decimal("60"))

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.carbohydrate_g == Decimal("60")

    async def test_maps_fat(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema(fat_g=Decimal("15"))

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry.fat_g == Decimal("15")

    async def test_uses_explicit_field_mapping(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        added_obj = session.add.call_args[0][0]
        assert isinstance(added_obj, NutritionLog)
        assert added_obj.user_id is not None
        assert added_obj.entry_id is not None
        assert added_obj.logged_date is not None

    async def test_does_not_blindly_unpack_model_dump(self):
        session = _make_session()
        session.flush = AsyncMock()
        NutritionLogRepository(session)
        _make_create_schema()

        import inspect

        import app.repositories.nutrition_log as mod

        source = inspect.getsource(mod)
        assert "data.model_dump()" not in source

    async def test_calls_session_add_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        session.add.assert_called_once()

    async def test_calls_session_flush_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        session.flush.assert_awaited_once()

    async def test_returns_created_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        entry = await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert entry is not None
        assert session.add.call_args[0][0] is entry

    async def test_never_commits(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        session.commit.assert_not_called()

    async def test_never_rolls_back(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        session.rollback.assert_not_called()

    async def test_never_closes_session(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        session.close.assert_not_called()


class TestCreateMutableAliasing:
    async def test_does_not_mutate_input_schema(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        data = _make_create_schema()

        await repo.create(
            user_id=uuid.uuid4(),
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert data.food_name is not None
        assert data.calories_kcal is not None


# ===========================================================================
# E. create — unique constraint violation
# ===========================================================================


class TestCreateUniqueConstraintViolation:
    def _make_orig(self, constraint_name: str = "uq_nutrition_logs_user_id_entry_id"):
        class FakeOrig:
            pass

        orig = FakeOrig()
        orig.constraint_name = constraint_name
        return orig

    async def test_raises_nutrition_log_entry_already_exists(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_safe_default_message(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        assert str(exc_info.value) == "A nutrition log entry with this identifier already exists."

    async def test_preserves_exception_chaining(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        assert isinstance(exc_info.value.__cause__, IntegrityError)

    async def test_no_raw_sql_in_domain_message(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        msg = str(exc_info.value)
        assert "INSERT" not in msg
        assert "nutrition_logs" not in msg

    async def test_no_constraint_name_in_domain_message(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        msg = str(exc_info.value)
        assert "uq_nutrition_logs_user_id_entry_id" not in msg
        assert "constraint" not in msg.lower()

    async def test_no_credentials_in_domain_message(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        msg = str(exc_info.value)
        assert "password" not in msg.lower()
        assert "secret" not in msg.lower()

    async def test_no_commit_on_conflict(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        session.commit.assert_not_called()

    async def test_add_called_once_before_conflict(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        session.add.assert_called_once()

    async def test_flush_attempted_exactly_once(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig()
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(NutritionLogEntryAlreadyExistsError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        session.flush.assert_awaited_once()


# ===========================================================================
# F. create — unrelated IntegrityError
# ===========================================================================


class TestCreateUnrelatedIntegrityError:
    def _make_orig(self, constraint_name: str):
        class FakeOrig:
            pass

        orig = FakeOrig()
        orig.constraint_name = constraint_name
        return orig

    async def test_different_unique_constraint(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig("uq_users_email")
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_foreign_key_constraint(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig("fk_nutrition_logs_user_id")
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_check_constraint_violation(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig("ck_nutrition_logs_calories_kcal_range")
        integrity_error = IntegrityError("INSERT INTO nutrition_logs...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_unknown_constraint_name(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        orig = self._make_orig("some_unknown_constraint")
        integrity_error = IntegrityError("INSERT INTO ...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_no_constraint_metadata(self):
        session = _make_session()
        repo = NutritionLogRepository(session)

        class FakeOrig:
            pass

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO ...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_orig_none(self):
        session = _make_session()
        repo = NutritionLogRepository(session)

        integrity_error = IntegrityError("INSERT INTO ...", {}, None)
        session.flush = AsyncMock(side_effect=integrity_error)

        data = _make_create_schema()
        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )


# ===========================================================================
# G. create — non-IntegrityError failure
# ===========================================================================


class TestCreateNonIntegrityFailure:
    async def test_original_exception_re_raised(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        data = _make_create_schema()
        with pytest.raises(RuntimeError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        assert "Unexpected error" in str(exc_info.value)

    async def test_no_swallowing(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        session.flush = AsyncMock(side_effect=ValueError("bad value"))

        data = _make_create_schema()
        with pytest.raises(ValueError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_no_commit_on_failure(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))

        data = _make_create_schema()
        with pytest.raises(RuntimeError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        session.commit.assert_not_called()

    async def test_no_close_on_failure(self):
        session = _make_session()
        repo = NutritionLogRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))

        data = _make_create_schema()
        with pytest.raises(RuntimeError):
            await repo.create(
                user_id=uuid.uuid4(),
                logged_date=date(2025, 1, 1),
                data=data,
            )

        session.close.assert_not_called()


# ===========================================================================
# H. delete
# ===========================================================================


class TestDelete:
    async def test_deletes_exact_supplied_object(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.delete.assert_awaited_once_with(entry)

    async def test_calls_delete_once(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.delete.assert_awaited_once()

    async def test_calls_flush_once(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.flush.assert_awaited_once()

    async def test_does_not_commit(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.commit.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.close.assert_not_called()

    async def test_does_not_refresh(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.refresh.assert_not_called()

    async def test_does_not_create_session(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session_factory_attr = getattr(session, "session_factory", None)
        if session_factory_attr is not None:
            session_factory_attr.assert_not_called()

    async def test_returns_none(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        result = await repo.delete(entry=entry)

        assert result is None

    async def test_re_raises_unexpected_failures(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock(side_effect=RuntimeError("delete failed"))
        repo = NutritionLogRepository(session)
        entry = _make_entry()

        with pytest.raises(RuntimeError) as exc_info:
            await repo.delete(entry=entry)

        assert "delete failed" in str(exc_info.value)
