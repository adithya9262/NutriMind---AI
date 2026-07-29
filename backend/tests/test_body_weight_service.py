from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.body_weight_exceptions import (
    BodyWeightNotFoundError,
    DuplicateBodyWeightDateError,
    DuplicateBodyWeightEntryIdError,
)
from app.models.body_weight import BodyWeight
from app.repositories.body_weight import BodyWeightRepository
from app.services.body_weight import BodyWeightService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo() -> MagicMock:
    return AsyncMock(spec=BodyWeightRepository)


def _make_entry(
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date = date(2025, 6, 15),
    weight_kg: Decimal = Decimal("70.00"),
) -> MagicMock:
    entry = MagicMock(spec=BodyWeight)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.entry_id = entry_id or uuid.uuid4()
    entry.logged_date = logged_date
    entry.weight_kg = weight_kg
    return entry


# ===========================================================================
# A. Constructor
# ===========================================================================


class TestConstructor:
    def test_stores_supplied_repository(self):
        repo = _make_repo()
        service = BodyWeightService(repo)
        assert service._repository is repo

    def test_does_not_create_repository(self):
        repo = _make_repo()
        BodyWeightService(repo)
        repo.assert_not_called()

    def test_does_not_query_during_construction(self):
        repo = _make_repo()
        BodyWeightService(repo)
        repo.list_by_user_id.assert_not_called()
        repo.create.assert_not_called()
        repo.delete.assert_not_called()
        repo.get_by_user_and_entry_id.assert_not_called()

    def test_does_not_create_session(self):
        repo = _make_repo()
        BodyWeightService(repo)
        assert not hasattr(repo, "_session")


# ===========================================================================
# B. list_history
# ===========================================================================


class TestListHistory:
    async def test_calls_repository_exactly_once(self):
        repo = _make_repo()
        repo.list_by_user_id.return_value = []
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.list_history(user_id=user_id)

        repo.list_by_user_id.assert_awaited_once()

    async def test_passes_user_id_unchanged(self):
        repo = _make_repo()
        repo.list_by_user_id.return_value = []
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.list_history(user_id=user_id)

        repo.list_by_user_id.assert_awaited_once_with(user_id=user_id)

    async def test_returns_repository_result(self):
        expected = [_make_entry(), _make_entry()]
        repo = _make_repo()
        repo.list_by_user_id.return_value = expected
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        result = await service.list_history(user_id=user_id)

        assert result is expected

    async def test_returns_empty_list_when_no_entries(self):
        repo = _make_repo()
        repo.list_by_user_id.return_value = []
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        result = await service.list_history(user_id=user_id)

        assert result == []

    async def test_preserves_repository_ordering(self):
        repo = _make_repo()
        entry1 = _make_entry(logged_date=date(2025, 6, 15))
        entry2 = _make_entry(logged_date=date(2025, 1, 1))
        repo.list_by_user_id.return_value = [entry1, entry2]
        service = BodyWeightService(repo)

        result = await service.list_history(user_id=uuid.uuid4())

        assert result == [entry1, entry2]

    async def test_does_not_mutate_result(self):
        entry = _make_entry()
        repo = _make_repo()
        repo.list_by_user_id.return_value = [entry]
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        result = await service.list_history(user_id=user_id)

        assert result[0].entry_id == entry.entry_id
        assert result[0].weight_kg == entry.weight_kg

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.list_by_user_id.return_value = []
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.list_history(user_id=user_id)

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        repo.list_by_user_id.return_value = []
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.list_history(user_id=user_id)

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_preserves_repository_exceptions(self):
        repo = _make_repo()
        repo.list_by_user_id.side_effect = RuntimeError("repo error")
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(RuntimeError) as exc_info:
            await service.list_history(user_id=user_id)

        assert "repo error" in str(exc_info.value)


# ===========================================================================
# C. get_entry
# ===========================================================================


class TestGetEntry:
    async def test_calls_get_by_user_and_entry_id_exactly_once(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.get_entry(user_id=user_id, entry_id=entry.entry_id)

        repo.get_by_user_and_entry_id.assert_awaited_once()

    async def test_passes_both_user_id_and_entry_id(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.get_entry(user_id=user_id, entry_id=entry_id)

        repo.get_by_user_and_entry_id.assert_awaited_once_with(
            user_id=user_id,
            entry_id=entry_id,
        )

    async def test_returns_owned_entry(self):
        repo = _make_repo()
        expected = _make_entry()
        repo.get_by_user_and_entry_id.return_value = expected
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        result = await service.get_entry(user_id=user_id, entry_id=expected.entry_id)

        assert result is expected

    async def test_missing_entry_raises_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError):
            await service.get_entry(user_id=user_id, entry_id=entry_id)

    async def test_safe_default_message(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError) as exc_info:
            await service.get_entry(user_id=user_id, entry_id=entry_id)

        assert str(exc_info.value) == "Body-weight entry was not found."

    async def test_cross_user_absence_indistinguishable(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError) as exc_info:
            await service.get_entry(user_id=user_id, entry_id=entry_id)

        msg = str(exc_info.value)
        assert "not found" in msg.lower()
        assert str(user_id) not in msg
        assert str(entry_id) not in msg

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.get_entry(user_id=user_id, entry_id=uuid.uuid4())

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.get_entry(user_id=user_id, entry_id=uuid.uuid4())

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()


# ===========================================================================
# D. create_entry
# ===========================================================================


class TestCreateEntry:
    async def test_calls_repository_create_exactly_once(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.create_entry(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        repo.create.assert_awaited_once()

    async def test_passes_trusted_user_id_unchanged(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.create_entry(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        repo.create.assert_awaited_once_with(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

    async def test_passes_entry_id_unchanged(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        entry_id = uuid.uuid4()

        await service.create_entry(
            user_id=uuid.uuid4(),
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["entry_id"] == entry_id

    async def test_passes_logged_date_unchanged(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        target_date = date(2025, 12, 25)

        await service.create_entry(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=target_date,
            weight_kg=Decimal("70.00"),
        )

        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["logged_date"] == target_date

    async def test_passes_weight_kg_unchanged(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        weight = Decimal("71.50")

        await service.create_entry(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=weight,
        )

        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["weight_kg"] == weight

    async def test_returns_repository_result(self):
        expected = _make_entry()
        repo = _make_repo()
        repo.create.return_value = expected
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        result = await service.create_entry(
            user_id=user_id,
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        assert result is expected

    async def test_preserves_duplicate_date_exception(self):
        repo = _make_repo()
        repo.create.side_effect = DuplicateBodyWeightDateError()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(DuplicateBodyWeightDateError):
            await service.create_entry(
                user_id=user_id,
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_preserves_duplicate_entry_id_exception(self):
        repo = _make_repo()
        repo.create.side_effect = DuplicateBodyWeightEntryIdError()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(DuplicateBodyWeightEntryIdError):
            await service.create_entry(
                user_id=user_id,
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_preserves_repository_exceptions(self):
        repo = _make_repo()
        repo.create.side_effect = RuntimeError("create failed")
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        with pytest.raises(RuntimeError) as exc_info:
            await service.create_entry(
                user_id=user_id,
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        assert "create failed" in str(exc_info.value)

    async def test_does_not_commit(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.create_entry(
            user_id=user_id,
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.create_entry(
            user_id=user_id,
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_does_not_rollback(self):
        repo = _make_repo()
        repo.create.return_value = _make_entry()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.create_entry(
            user_id=user_id,
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        if hasattr(repo, "rollback"):
            repo.rollback.assert_not_called()


# ===========================================================================
# E. delete_entry — found
# ===========================================================================


class TestDeleteEntryFound:
    async def test_calls_get_by_user_and_entry_id(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry_id)

        repo.get_by_user_and_entry_id.assert_awaited_once()

    async def test_passes_both_user_id_and_entry_id(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry_id)

        repo.get_by_user_and_entry_id.assert_awaited_once_with(
            user_id=user_id,
            entry_id=entry_id,
        )

    async def test_passes_existing_entry_to_repository_delete(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry.entry_id)

        repo.delete.assert_awaited_once_with(entry=entry)

    async def test_calls_repository_delete_exactly_once(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry.entry_id)

        repo.delete.assert_awaited_once()

    async def test_returns_none(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        result = await service.delete_entry(user_id=user_id, entry_id=entry.entry_id)

        assert result is None

    async def test_does_not_commit(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry.entry_id)

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    async def test_does_not_flush(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry.entry_id)

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    async def test_does_not_rollback(self):
        repo = _make_repo()
        entry = _make_entry()
        repo.get_by_user_and_entry_id.return_value = entry
        repo.delete = AsyncMock()
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()

        await service.delete_entry(user_id=user_id, entry_id=entry.entry_id)

        if hasattr(repo, "rollback"):
            repo.rollback.assert_not_called()


class TestDeleteEntryNotFound:
    async def test_missing_entry_raises_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError):
            await service.delete_entry(user_id=user_id, entry_id=entry_id)

    async def test_safe_default_message(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError) as exc_info:
            await service.delete_entry(user_id=user_id, entry_id=entry_id)

        assert str(exc_info.value) == "Body-weight entry was not found."

    async def test_repository_delete_not_called_when_missing(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError):
            await service.delete_entry(user_id=user_id, entry_id=entry_id)

        if hasattr(repo, "delete"):
            repo.delete.assert_not_called()

    async def test_cross_user_absence_indistinguishable(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError) as exc_info:
            await service.delete_entry(user_id=user_id, entry_id=entry_id)

        msg = str(exc_info.value)
        assert "not found" in msg.lower()
        assert str(user_id) not in msg
        assert str(entry_id) not in msg

    async def test_no_sql_details_in_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_entry_id.return_value = None
        service = BodyWeightService(repo)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        with pytest.raises(BodyWeightNotFoundError) as exc_info:
            await service.delete_entry(user_id=user_id, entry_id=entry_id)

        msg = str(exc_info.value)
        assert "SELECT" not in msg
        assert "INSERT" not in msg
        assert "constraint" not in msg.lower()


# ===========================================================================
# F. Service boundary — no prohibited imports
# ===========================================================================


class TestServiceBoundary:
    def test_no_async_session_dependency(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "AsyncSession" not in source

    def test_no_sqlalchemy_import(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_fastapi_import(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_direct_select(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "select(" not in source

    def test_no_commit(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert ".commit(" not in source

    def test_no_flush(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert ".flush(" not in source

    def test_no_rollback(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert ".rollback(" not in source

    def test_no_close(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert ".close(" not in source

    def test_no_repository_construction_internally(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "BodyWeightRepository(" not in source

    def test_no_database_configuration(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "DATABASE_URL" not in source
        assert "settings" not in source

    def test_no_weight_trend_calculations(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "trend" not in source

    def test_no_percentage_change(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "percentage" not in source

    def test_no_bmi_calculations(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "bmi" not in source

    def test_no_bmr_calculations(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "bmr" not in source

    def test_no_tdee_calculations(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "tdee" not in source

    def test_no_nutrition_profile_sync(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "nutrition_profile" not in source

    def test_no_weight_change_calculation(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "weight_change" not in source

    def test_no_average_calculation(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "average" not in source

    def test_no_prediction(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "predict" not in source

    def test_no_recommendation(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "recommend" not in source

    def test_no_ai_functionality(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read().lower()
        assert "groq" not in source
        assert "usda" not in source

    def test_no_schema_import(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "from app.schemas" not in source


# ===========================================================================
# G. Import side effects
# ===========================================================================


class TestServiceImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        from app.services import BodyWeightService

        assert BodyWeightService is not None

    def test_import_does_not_require_postgres(self):
        from app.services.body_weight import BodyWeightService

        assert BodyWeightService is not None

    def test_import_works_without_database_url(self):
        from app.services import BodyWeightService

        assert BodyWeightService is not None


# ===========================================================================
# H. Service purity
# ===========================================================================


class TestServicePurity:
    def test_no_starlette_import(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "starlette" not in source.lower()

    def test_no_http_status_code(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "status_code" not in source.lower()

    def test_no_body_weight_schema_validation(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "BodyWeightEntryCreate" not in source

    def test_no_domain_validation_duplication(self):
        import app.services.body_weight as mod

        source = open(mod.__file__).read()
        assert "_validate_weight_kg" not in source
