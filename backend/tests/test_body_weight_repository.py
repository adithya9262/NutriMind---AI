from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.body_weight_exceptions import (
    DuplicateBodyWeightDateError,
    DuplicateBodyWeightEntryIdError,
)
from app.models.body_weight import BodyWeight
from app.repositories.body_weight import BodyWeightRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


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
    def test_stores_supplied_session(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        assert repo._session is session

    def test_does_not_create_another_session(self):
        session = _make_session()
        BodyWeightRepository(session)
        session.assert_not_called()

    def test_does_not_connect_during_construction(self):
        session = _make_session()
        BodyWeightRepository(session)
        session.execute.assert_not_called()

    def test_does_not_create_engine(self):
        session = _make_session()
        BodyWeightRepository(session)
        assert not hasattr(session, "engine")


# ===========================================================================
# B. list_by_user_id — general
# ===========================================================================


class TestListByUserIdGeneral:
    async def test_filters_by_user_id(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        user_id = uuid.uuid4()
        await repo.list_by_user_id(user_id=user_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled

    async def test_executes_exactly_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.execute.assert_awaited_once()

    async def test_returns_list(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert isinstance(result, list)

    async def test_returns_new_list(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        result1 = await repo.list_by_user_id(user_id=uuid.uuid4())
        result2 = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert result1 is not result2

    async def test_returns_empty_list_when_no_rows(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert result == []

    async def test_returns_all_matching_rows(self):
        session = _make_session()
        entry1 = _make_entry()
        entry2 = _make_entry()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [entry1, entry2]
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert len(result) == 2
        assert result[0] is entry1
        assert result[1] is entry2

    async def test_does_not_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.close.assert_not_called()

    async def test_does_not_refresh(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.refresh.assert_not_called()

    async def test_re_raises_unexpected_execution_exceptions(self):
        session = _make_session()
        session.execute = AsyncMock(side_effect=Exception("DB error"))

        repo = BodyWeightRepository(session)
        with pytest.raises(Exception) as exc_info:
            await repo.list_by_user_id(user_id=uuid.uuid4())

        assert "DB error" in str(exc_info.value)


class TestListByUserIdOrdering:
    async def test_uses_logged_date_descending(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "DESC" in compiled.upper()

    async def test_preserves_deterministic_database_ordering(self):
        session = _make_session()
        entry_a = _make_entry()
        entry_b = _make_entry()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [entry_a, entry_b]
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert result == [entry_a, entry_b]


# ===========================================================================
# C. get_by_user_and_entry_id
# ===========================================================================


class TestGetByUserAndEntryId:
    async def test_filters_by_both_user_id_and_entry_id(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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

        repo = BodyWeightRepository(session)
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
    async def test_creates_body_weight(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        entry = await repo.create(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        assert isinstance(entry, BodyWeight)

    async def test_sets_trusted_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        user_id = uuid.uuid4()
        entry_id = uuid.uuid4()

        entry = await repo.create(
            user_id=user_id,
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        assert entry.user_id == user_id

    async def test_maps_caller_owned_entry_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry_id = uuid.uuid4()

        entry = await repo.create(
            user_id=uuid.uuid4(),
            entry_id=entry_id,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        assert entry.entry_id == entry_id

    async def test_maps_logged_date(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        target_date = date(2025, 7, 4)

        entry = await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=target_date,
            weight_kg=Decimal("70.00"),
        )

        assert entry.logged_date == target_date

    async def test_maps_decimal_weight(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        weight = Decimal("70.50")

        entry = await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=weight,
        )

        assert entry.weight_kg == weight

    async def test_calls_session_add_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)

        await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        session.add.assert_called_once()

    async def test_calls_session_flush_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)

        await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        session.flush.assert_awaited_once()

    async def test_returns_created_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)

        entry = await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        assert entry is not None
        assert session.add.call_args[0][0] is entry

    async def test_never_commits(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)

        await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        session.commit.assert_not_called()

    async def test_never_rolls_back(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)

        await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        session.rollback.assert_not_called()

    async def test_never_closes_session(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)

        await repo.create(
            user_id=uuid.uuid4(),
            entry_id=uuid.uuid4(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )

        session.close.assert_not_called()

    async def test_does_not_use_model_dump(self):
        import inspect

        import app.repositories.body_weight as mod

        source = inspect.getsource(mod)
        assert "model_dump" not in source


class TestCreateInputIntegrity:
    async def test_does_not_mutate_caller_data(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry_id = uuid.uuid4()
        logged_date = date(2025, 6, 15)
        weight_kg = Decimal("70.00")

        await repo.create(
            user_id=uuid.uuid4(),
            entry_id=entry_id,
            logged_date=logged_date,
            weight_kg=weight_kg,
        )

        assert entry_id is not None
        assert logged_date is not None
        assert weight_kg is not None


# ===========================================================================
# E. create — unique constraint violation
# ===========================================================================


class TestCreateUniqueConstraintViolation:
    def _make_orig(self, constraint_name: str):
        class FakeOrig:
            pass

        orig = FakeOrig()
        orig.constraint_name = constraint_name
        return orig

    async def test_duplicate_logged_date_raises_duplicate_body_weight_date_error(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_duplicate_entry_id_raises_duplicate_body_weight_entry_id_error(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_entry_id")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightEntryIdError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_safe_default_message_for_date_duplicate(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        assert str(exc_info.value) == "A body-weight entry already exists for the selected date."

    async def test_safe_default_message_for_entry_id_duplicate(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_entry_id")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightEntryIdError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        assert str(exc_info.value) == "A body-weight entry already exists with this entry ID."

    async def test_preserves_exception_chaining(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        assert isinstance(exc_info.value.__cause__, IntegrityError)

    async def test_no_raw_sql_in_domain_message(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        msg = str(exc_info.value)
        assert "INSERT" not in msg
        assert "body_weights" not in msg

    async def test_no_constraint_name_in_domain_message(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        msg = str(exc_info.value)
        assert "uq_body_weights_user_id_logged_date" not in msg
        assert "constraint" not in msg.lower()

    async def test_no_commit_on_conflict(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        session.commit.assert_not_called()

    async def test_add_called_once_before_conflict(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        session.add.assert_called_once()

    async def test_flush_attempted_exactly_once(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_body_weights_user_id_logged_date")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(DuplicateBodyWeightDateError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
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

    async def test_unknown_unique_constraint(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("uq_users_email")
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_foreign_key_constraint(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("fk_body_weights_user_id")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_check_constraint_violation(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("ck_body_weights_weight_kg_range")
        integrity_error = IntegrityError("INSERT INTO body_weights...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_unknown_constraint_name(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        orig = self._make_orig("some_unknown_constraint")
        integrity_error = IntegrityError("INSERT INTO ...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_no_constraint_metadata(self):
        session = _make_session()
        repo = BodyWeightRepository(session)

        class FakeOrig:
            pass

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO ...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_orig_none(self):
        session = _make_session()
        repo = BodyWeightRepository(session)

        integrity_error = IntegrityError("INSERT INTO ...", {}, None)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )


# ===========================================================================
# G. create — non-IntegrityError failure
# ===========================================================================


class TestCreateNonIntegrityFailure:
    async def test_original_exception_re_raised(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        with pytest.raises(RuntimeError) as exc_info:
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        assert "Unexpected error" in str(exc_info.value)

    async def test_no_swallowing(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        session.flush = AsyncMock(side_effect=ValueError("bad value"))

        with pytest.raises(ValueError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    async def test_no_commit_on_failure(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))

        with pytest.raises(RuntimeError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

        session.commit.assert_not_called()

    async def test_no_close_on_failure(self):
        session = _make_session()
        repo = BodyWeightRepository(session)
        session.flush = AsyncMock(side_effect=RuntimeError("fail"))

        with pytest.raises(RuntimeError):
            await repo.create(
                user_id=uuid.uuid4(),
                entry_id=uuid.uuid4(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
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
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.delete.assert_awaited_once_with(entry)

    async def test_calls_delete_once(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.delete.assert_awaited_once()

    async def test_calls_flush_once(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.flush.assert_awaited_once()

    async def test_does_not_commit(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.commit.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.close.assert_not_called()

    async def test_does_not_refresh(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        await repo.delete(entry=entry)

        session.refresh.assert_not_called()

    async def test_returns_none(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        result = await repo.delete(entry=entry)

        assert result is None

    async def test_re_raises_unexpected_failures(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock(side_effect=RuntimeError("delete failed"))
        repo = BodyWeightRepository(session)
        entry = _make_entry()

        with pytest.raises(RuntimeError) as exc_info:
            await repo.delete(entry=entry)

        assert "delete failed" in str(exc_info.value)
