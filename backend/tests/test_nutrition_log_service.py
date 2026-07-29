from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.nutrition_log_exceptions import (
    NutritionLogEntryAlreadyExistsError,
    NutritionLogEntryNotFoundError,
)
from app.core.nutrition_logs import MealType
from app.models.nutrition_log import NutritionLog
from app.repositories.nutrition_log import NutritionLogRepository
from app.schemas.nutrition_logs import NutritionLogEntryCreate
from app.services.nutrition_log import NutritionLogService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo() -> MagicMock:
    return AsyncMock(spec=NutritionLogRepository)


def _make_entry() -> MagicMock:
    entry = MagicMock(spec=NutritionLog)
    entry.id = uuid.uuid4()
    entry.user_id = uuid.uuid4()
    entry.entry_id = uuid.uuid4()
    entry.logged_date = date(2025, 1, 1)
    entry.food_name = "Oatmeal"
    entry.meal_type = MealType.BREAKFAST
    entry.serving_description = "1 bowl"
    entry.calories_kcal = Decimal("300.00")
    entry.protein_g = Decimal("10.00")
    entry.carbohydrate_g = Decimal("50.00")
    entry.fat_g = Decimal("5.00")
    return entry


def _make_create_schema() -> NutritionLogEntryCreate:
    return NutritionLogEntryCreate(
        entry_id=uuid.uuid4(),
        food_name="Oatmeal",
        meal_type=MealType.BREAKFAST,
        serving_description="1 bowl",
        calories_kcal=Decimal("300"),
        protein_g=Decimal("10"),
        carbohydrate_g=Decimal("50"),
        fat_g=Decimal("5"),
    )


# ===========================================================================
# A. Constructor
# ===========================================================================


class TestConstructor:
    def test_stores_supplied_repository(self):
        repo = _make_repo()
        service = NutritionLogService(repo)
        assert service._repository is repo

    def test_does_not_create_repository(self):
        repo = _make_repo()
        NutritionLogService(repo)
        repo.assert_not_called()

    def test_does_not_query_during_construction(self):
        repo = _make_repo()
        NutritionLogService(repo)
        repo.list_by_user_and_date.assert_not_called()
        repo.create.assert_not_called()
        repo.delete.assert_not_called()
        repo.get_by_user_and_entry_id.assert_not_called()

    def test_does_not_create_session(self):
        repo = _make_repo()
        NutritionLogService(repo)
        assert not hasattr(repo, "_session")


# ===========================================================================
# B. list_daily_entries
# ===========================================================================


class TestListDailyEntries:
    async def test_calls_repository_exactly_once(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        logged_date = date(2025, 1, 1)

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=logged_date,
        )

        repo.list_by_user_and_date.assert_awaited_once()

    async def test_passes_user_id_unchanged(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        logged_date = date(2025, 1, 1)

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=logged_date,
        )

        repo.list_by_user_and_date.assert_awaited_once_with(
            user_id=user_id,
            logged_date=logged_date,
        )

    async def test_passes_logged_date_unchanged(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        logged_date = date(2025, 7, 4)

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=logged_date,
        )

        repo.list_by_user_and_date.assert_awaited_once_with(
            user_id=user_id,
            logged_date=logged_date,
        )

    async def test_returns_repository_result(self):
        expected = [_make_entry(), _make_entry()]
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = expected
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        result = await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        assert result is expected

    async def test_returns_empty_list_when_no_entries(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        result = await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        assert result == []

    async def test_does_not_mutate_result(self):
        entry = _make_entry()
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = [entry]
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        result = await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        assert result[0].food_name == entry.food_name
        assert result[0].calories_kcal == entry.calories_kcal

    async def test_does_not_calculate_totals(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        import inspect

        import app.services.nutrition_log as mod

        source = inspect.getsource(mod)
        assert "calculate_daily_nutrition_totals" not in source

    async def test_does_not_compare_against_targets(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        import inspect

        import app.services.nutrition_log as mod

        source = inspect.getsource(mod)
        assert "target" not in source.lower()

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        repo.list_by_user_and_date.return_value = []
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.list_daily_entries(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
        )

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_preserves_repository_exceptions(self):
        repo = _make_repo()
        repo.list_by_user_and_date.side_effect = RuntimeError("repo error")
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(RuntimeError) as exc_info:
            await service.list_daily_entries(
                user_id=user_id,
                logged_date=date(2025, 1, 1),
            )

        assert "repo error" in str(exc_info.value)


# ===========================================================================
# C. create_entry
# ===========================================================================


class TestCreateEntry:
    async def test_calls_repository_create_exactly_once(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        repo.create.assert_awaited_once()

    async def test_passes_trusted_user_id_unchanged(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        repo.create.assert_awaited_once_with(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

    async def test_passes_logged_date_unchanged(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()
        target_date = date(2025, 12, 25)

        await service.create_entry(
            user_id=user_id,
            logged_date=target_date,
            data=data,
        )

        repo.create.assert_awaited_once_with(
            user_id=user_id,
            logged_date=target_date,
            data=data,
        )

    async def test_passes_exact_schema_object(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["data"] is data

    async def test_returns_repository_result(self):
        expected = _make_entry()
        repo = _make_repo()
        repo.create.return_value = expected
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        result = await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        assert result is expected

    async def test_preserves_duplicate_entry_domain_exception(self):
        repo = _make_repo()
        repo.create.side_effect = NutritionLogEntryAlreadyExistsError()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(NutritionLogEntryAlreadyExistsError):
            await service.create_entry(
                user_id=user_id,
                logged_date=date(2025, 1, 1),
                data=data,
            )

    async def test_does_not_transform_nutrition_values(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        import inspect

        import app.services.nutrition_log as mod

        source = inspect.getsource(mod)
        assert "Decimal(" not in source.replace("from __future__", "")

    async def test_does_not_calculate_nutrition_values(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        import inspect

        import app.services.nutrition_log as mod

        source = inspect.getsource(mod)
        assert "calculate" not in source.lower()

    async def test_does_not_call_summary_builders(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        import inspect

        import app.services.nutrition_log as mod

        source = inspect.getsource(mod)
        assert "summarize" not in source.lower()

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_does_not_rollback(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        await service.create_entry(
            user_id=user_id,
            logged_date=date(2025, 1, 1),
            data=data,
        )

        if hasattr(repo, "rollback"):
            repo.rollback.assert_not_called()

    async def test_preserves_repository_exceptions(self):
        repo = _make_repo()
        repo.create.side_effect = RuntimeError("create failed")
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        data = _make_create_schema()

        with pytest.raises(RuntimeError) as exc_info:
            await service.create_entry(
                user_id=user_id,
                logged_date=date(2025, 1, 1),
                data=data,
            )

        assert "create failed" in str(exc_info.value)


# ===========================================================================
# D. delete_entry
# ===========================================================================


class TestDeleteEntryFound:
    async def test_calls_get_by_user_and_entry_id(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry_id,
        )

        repo.get_by_user_and_entry_id.assert_awaited_once()

    async def test_passes_both_user_id_and_entry_id(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry_id,
        )

        repo.get_by_user_and_entry_id.assert_awaited_once_with(
            user_id=user_id,
            entry_id=entry_id,
        )

    async def test_passes_existing_entry_to_repository_delete(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry.entry_id,
        )

        repo.delete.assert_awaited_once_with(entry=entry)

    async def test_calls_repository_delete_exactly_once(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry.entry_id,
        )

        repo.delete.assert_awaited_once()

    async def test_returns_none(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        result = await service.delete_entry(
            user_id=user_id,
            entry_id=entry.entry_id,
        )

        assert result is None

    async def test_does_not_commit(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry.entry_id,
        )

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry.entry_id,
        )

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_does_not_rollback(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(
            user_id=user_id,
            entry_id=entry.entry_id,
        )

        if hasattr(repo, "rollback"):
            repo.rollback.assert_not_called()


class TestDeleteEntryNotFound:
    async def test_missing_entry_raises_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(NutritionLogEntryNotFoundError):
            await service.delete_entry(
                user_id=user_id,
                entry_id=entry_id,
            )

    async def test_safe_default_message(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(NutritionLogEntryNotFoundError) as exc_info:
            await service.delete_entry(
                user_id=user_id,
                entry_id=entry_id,
            )

        assert str(exc_info.value) == "Nutrition log entry was not found."

    async def test_repository_delete_not_called_when_missing(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(NutritionLogEntryNotFoundError):
            await service.delete_entry(
                user_id=user_id,
                entry_id=entry_id,
            )

        if hasattr(repo, "delete"):
            repo.delete.assert_not_called()

    async def test_cross_user_absence_indistinguishable(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(NutritionLogEntryNotFoundError) as exc_info:
            await service.delete_entry(
                user_id=user_id,
                entry_id=entry_id,
            )

        msg = str(exc_info.value)
        assert "not found" in msg.lower()
        assert str(user_id) not in msg
        assert str(entry_id) not in msg

    async def test_no_sql_details_in_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = NutritionLogService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(NutritionLogEntryNotFoundError) as exc_info:
            await service.delete_entry(
                user_id=user_id,
                entry_id=entry_id,
            )

        msg = str(exc_info.value)
        assert "SELECT" not in msg
        assert "INSERT" not in msg
        assert "constraint" not in msg.lower()


# ===========================================================================
# E. Service boundary — no prohibited imports
# ===========================================================================


class TestServiceBoundary:
    def test_no_async_session_dependency(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "AsyncSession" not in source

    def test_no_sqlalchemy_import(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_fastapi_import(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_direct_select(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "select(" not in source

    def test_no_commit(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert ".commit(" not in source

    def test_no_flush(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert ".flush(" not in source

    def test_no_rollback(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert ".rollback(" not in source

    def test_no_close(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert ".close(" not in source

    def test_no_repository_construction_internally(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "NutritionLogRepository(" not in source

    def test_no_database_configuration(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read()
        assert "DATABASE_URL" not in source
        assert "settings" not in source

    def test_no_aggregation_calls(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read().lower()
        assert "summarize_daily_nutrition_log" not in source
        assert "calculate_daily_nutrition_totals" not in source

    def test_no_target_comparison(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read().lower()
        assert "compare" not in source
        assert "remaining" not in source

    def test_no_ai_functionality(self):
        import app.services.nutrition_log as mod

        source = open(mod.__file__).read().lower()
        assert "groq" not in source
        assert "usda" not in source
        assert "recommend" not in source


# ===========================================================================
# F. Import side effects
# ===========================================================================


class TestServiceImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        from app.services import NutritionLogService

        assert NutritionLogService is not None

    def test_import_does_not_require_postgres(self):
        from app.services.nutrition_log import NutritionLogService

        assert NutritionLogService is not None

    def test_import_works_without_database_url(self):
        from app.services import NutritionLogService

        assert NutritionLogService is not None
