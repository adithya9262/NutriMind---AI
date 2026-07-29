from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.task_exceptions import (
    DuplicateTaskIdError,
)
from app.core.tasks import (
    Task,
    TaskPriority,
    TaskStatus,
    create_task,
)
from app.models.task import Task as TaskORM
from app.repositories.task import TaskRepository

_TZ = UTC


class _FakeOrig:
    def __init__(self, constraint_name: str | None = None, text: str = "") -> None:
        self.constraint_name = constraint_name
        self._text = text

    def __str__(self) -> str:
        return self._text


def _integrity_error(orig: object) -> IntegrityError:
    return IntegrityError("statement", {}, orig)


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_task_orm(
    user_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    title: str = "Buy groceries",
    description: str | None = "Milk and eggs",
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.PENDING,
    due_date: date | None = None,
    completed_at: datetime | None = None,
) -> TaskORM:
    return TaskORM(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        task_id=task_id or uuid.uuid4(),
        title=title,
        description=description,
        priority=priority,
        status=status,
        due_date=due_date,
        completed_at=completed_at,
    )


def _domain_task(
    task_id: uuid.UUID | None = None,
    title: str = "Buy groceries",
    description: str | None = "Milk and eggs",
    priority: TaskPriority = TaskPriority.MEDIUM,
    due_date: date | None = None,
) -> Task:
    return create_task(
        task_id=task_id or uuid.uuid4(),
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )


# ===========================================================================
# A. Module and exports
# ===========================================================================


class TestModuleExports:
    def test_module_imports(self):
        import app.repositories.task as mod

        assert mod is not None

    def test_class_exists(self):
        from app.repositories.task import TaskRepository

        assert TaskRepository is not None

    def test_exported_from_app_repositories(self):
        from app.repositories import TaskRepository

        assert TaskRepository is not None

    def test_single_implementation(self):
        import app.repositories.task as mod

        assert mod.TaskRepository is not None
        assert not hasattr(mod, "TaskRepositoryBase")
        assert not hasattr(mod, "TasksRepository")

    def test_no_duplicate_module(self):
        import os

        assert os.path.exists("app/repositories/task.py")


# ===========================================================================
# B. Constructor
# ===========================================================================


class TestConstructor:
    def test_stores_supplied_session(self):
        session = _make_session()
        repo = TaskRepository(session)
        assert repo._session is session

    def test_does_not_create_another_session(self):
        session = _make_session()
        TaskRepository(session)
        session.assert_not_called()

    def test_does_not_connect_during_construction(self):
        session = _make_session()
        TaskRepository(session)
        session.execute.assert_not_called()

    def test_does_not_create_engine(self):
        session = _make_session()
        TaskRepository(session)
        assert not hasattr(session, "engine")


# ===========================================================================
# C. list_by_user_id
# ===========================================================================


class TestListByUserId:
    async def test_filters_by_user_id(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        user_id = uuid.uuid4()
        await repo.list_by_user_id(user_id=user_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled

    async def test_does_not_query_globally(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        user_id = uuid.uuid4()
        await repo.list_by_user_id(user_id=user_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "WHERE" in compiled
        assert "user_id" in compiled

    async def test_executes_exactly_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.execute.assert_awaited_once()

    async def test_returns_list(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert isinstance(result, list)

    async def test_empty_result(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert result == []

    async def test_returns_orm_rows(self):
        session = _make_session()
        rows = [_make_task_orm(), _make_task_orm()]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = rows
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        result = await repo.list_by_user_id(user_id=uuid.uuid4())

        assert result == rows
        assert all(isinstance(r, TaskORM) for r in result)

    async def test_no_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.commit.assert_not_called()

    async def test_no_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.rollback.assert_not_called()

    async def test_no_refresh(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.refresh.assert_not_called()

    async def test_no_add_on_list(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.list_by_user_id(user_id=uuid.uuid4())

        session.add.assert_not_called()


# ===========================================================================
# D. get_by_user_and_task_id
# ===========================================================================


class TestGetByUserAndTaskId:
    async def test_both_predicates_included(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled
        assert "task_id" in compiled

    async def test_executes_exactly_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        session.execute.assert_awaited_once()

    async def test_found_result(self):
        session = _make_session()
        row = _make_task_orm()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = row
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        result = await repo.get_by_user_and_task_id(user_id=row.user_id, task_id=row.task_id)

        assert result is row

    async def test_missing_returns_none(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        result = await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        assert result is None

    async def test_wrong_user_applies_both_predicates(self):
        session = _make_session()
        row = _make_task_orm()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = row
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=row.task_id)

        call_args = session.execute.call_args[0][0]
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert "user_id" in compiled
        assert "task_id" in compiled

    async def test_no_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        session.commit.assert_not_called()

    async def test_no_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        session.rollback.assert_not_called()

    async def test_no_refresh(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = TaskRepository(session)
        await repo.get_by_user_and_task_id(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        session.refresh.assert_not_called()


# ===========================================================================
# E. create
# ===========================================================================


class TestCreate:
    async def test_requires_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)
        task = _domain_task()

        await repo.create(user_id=uuid.uuid4(), task=task)

        added = session.add.call_args[0][0]
        assert isinstance(added, TaskORM)

    async def test_maps_all_seven_fields(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        completed = datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ)
        task = Task(
            task_id=task_id,
            title="Task A",
            description="Desc",
            priority=TaskPriority.HIGH,
            status=TaskStatus.COMPLETED,
            due_date=date(2025, 7, 1),
            completed_at=completed,
        )

        await repo.create(user_id=user_id, task=task)

        added = session.add.call_args[0][0]
        assert added.task_id == task_id
        assert added.title == "Task A"
        assert added.description == "Desc"
        assert added.priority is TaskPriority.HIGH
        assert added.status is TaskStatus.COMPLETED
        assert added.due_date == date(2025, 7, 1)
        assert added.completed_at == completed

    async def test_maps_user_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        user_id = uuid.uuid4()
        task = _domain_task()

        await repo.create(user_id=user_id, task=task)

        added = session.add.call_args[0][0]
        assert added.user_id == user_id

    async def test_does_not_generate_new_public_task_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        task_id = uuid.uuid4()
        task = _domain_task(task_id=task_id)

        result = await repo.create(user_id=uuid.uuid4(), task=task)

        assert result.task_id == task_id

    async def test_does_not_manually_set_orm_id(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        task = _domain_task()

        await repo.create(user_id=uuid.uuid4(), task=task)

        added = session.add.call_args[0][0]
        # We never pass an explicit id; the model default is applied later
        # by the session at flush time, not by the repository.
        assert added.id is None

    async def test_adds_exactly_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        session.add.assert_called_once()

    async def test_flushes_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        session.flush.assert_awaited_once()

    async def test_returns_created_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        task = _domain_task()
        result = await repo.create(user_id=uuid.uuid4(), task=task)

        assert isinstance(result, TaskORM)
        assert result.task_id == task.task_id

    async def test_no_commit(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        session.commit.assert_not_called()

    async def test_no_rollback(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        session.rollback.assert_not_called()

    async def test_no_refresh(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        session.refresh.assert_not_called()

    async def test_input_domain_task_unchanged(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        task = _domain_task(title="Original")
        await repo.create(user_id=uuid.uuid4(), task=task)

        assert task.title == "Original"


# ===========================================================================
# F. Duplicate translation
# ===========================================================================


class TestDuplicateTranslation:
    async def test_duplicate_becomes_duplicate_task_id_error(self):
        session = _make_session()
        session.flush = AsyncMock(
            side_effect=_integrity_error(_FakeOrig(constraint_name="uq_tasks_user_id_task_id"))
        )
        repo = TaskRepository(session)

        with pytest.raises(DuplicateTaskIdError):
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

    async def test_duplicate_safe_message(self):
        session = _make_session()
        session.flush = AsyncMock(
            side_effect=_integrity_error(_FakeOrig(constraint_name="uq_tasks_user_id_task_id"))
        )
        repo = TaskRepository(session)

        with pytest.raises(DuplicateTaskIdError) as excinfo:
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        assert str(excinfo.value) == "A task with this task ID already exists."

    async def test_duplicate_message_has_no_sql(self):
        session = _make_session()
        session.flush = AsyncMock(
            side_effect=_integrity_error(_FakeOrig(constraint_name="uq_tasks_user_id_task_id"))
        )
        repo = TaskRepository(session)

        with pytest.raises(DuplicateTaskIdError) as excinfo:
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        text = str(excinfo.value)
        assert "uq_tasks_user_id_task_id" not in text
        assert "user_id" not in text
        assert "task_id" not in text

    async def test_exception_chaining_preserved(self):
        session = _make_session()
        orig_exc = _integrity_error(_FakeOrig(constraint_name="uq_tasks_user_id_task_id"))
        session.flush = AsyncMock(side_effect=orig_exc)
        repo = TaskRepository(session)

        with pytest.raises(DuplicateTaskIdError) as excinfo:
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        assert excinfo.value.__cause__ is orig_exc

    async def test_no_rollback_on_duplicate(self):
        session = _make_session()
        session.flush = AsyncMock(
            side_effect=_integrity_error(_FakeOrig(constraint_name="uq_tasks_user_id_task_id"))
        )
        repo = TaskRepository(session)

        with pytest.raises(DuplicateTaskIdError):
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

        session.rollback.assert_not_called()

    async def test_unrelated_integrity_error_not_misclassified(self):
        session = _make_session()
        session.flush = AsyncMock(
            side_effect=_integrity_error(_FakeOrig(constraint_name="other_constraint"))
        )
        repo = TaskRepository(session)

        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

    async def test_unrelated_integrity_error_fallback_text(self):
        session = _make_session()
        session.flush = AsyncMock(
            side_effect=_integrity_error(
                _FakeOrig(constraint_name=None, text="some other violation")
            )
        )
        repo = TaskRepository(session)

        with pytest.raises(IntegrityError):
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())

    async def test_non_integrity_error_propagates(self):
        session = _make_session()
        session.flush = AsyncMock(side_effect=ValueError("boom"))
        repo = TaskRepository(session)

        with pytest.raises(ValueError):
            await repo.create(user_id=uuid.uuid4(), task=_domain_task())


# ===========================================================================
# G. delete
# ===========================================================================


class TestDelete:
    async def test_accepts_loaded_orm_task(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        entry = _make_task_orm()
        await repo.delete(task=entry)

        session.delete.assert_awaited_once()

    async def test_deletes_exact_object(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        entry = _make_task_orm()
        await repo.delete(task=entry)

        assert session.delete.call_args[0][0] is entry

    async def test_flushes_once(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.delete(task=_make_task_orm())

        session.flush.assert_awaited_once()

    async def test_no_unscoped_lookup(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.delete(task=_make_task_orm())

        session.execute.assert_not_called()

    async def test_no_commit(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.delete(task=_make_task_orm())

        session.commit.assert_not_called()

    async def test_no_rollback(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.delete(task=_make_task_orm())

        session.rollback.assert_not_called()

    async def test_no_refresh(self):
        session = _make_session()
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.delete(task=_make_task_orm())

        session.refresh.assert_not_called()


# ===========================================================================
# H. update / save behavior
# ===========================================================================


class TestUpdate:
    async def test_accepts_loaded_orm_object(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        entry = _make_task_orm()
        await repo.update(task=entry)

        session.flush.assert_awaited_once()

    async def test_does_not_perform_unscoped_lookup(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.update(task=_make_task_orm())

        session.execute.assert_not_called()

    async def test_flushes_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        entry = _make_task_orm()
        result = await repo.update(task=entry)

        session.flush.assert_awaited_once()
        assert result is entry

    async def test_no_commit(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.update(task=_make_task_orm())

        session.commit.assert_not_called()

    async def test_no_rollback(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.update(task=_make_task_orm())

        session.rollback.assert_not_called()

    async def test_no_refresh(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = TaskRepository(session)

        await repo.update(task=_make_task_orm())

        session.refresh.assert_not_called()


# ===========================================================================
# I. Source boundaries
# ===========================================================================


class TestSourceBoundaries:
    def test_no_commit_text(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "session.commit(" not in source
        assert "self._session.commit(" not in source

    def test_no_rollback_text(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "session.rollback(" not in source
        assert "self._session.rollback(" not in source

    def test_no_refresh_text(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "session.refresh(" not in source
        assert "self._session.refresh(" not in source

    def test_no_fastapi_import(self):
        import inspect

        assert "fastapi" not in inspect.getsource(TaskRepository).lower()

    def test_no_starlette_import(self):
        import inspect

        assert "starlette" not in inspect.getsource(TaskRepository).lower()

    def test_no_http_exception(self):
        import inspect

        assert "httpexception" not in inspect.getsource(TaskRepository).lower()

    def test_no_api_router_import(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_api_schema_import(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "from app.schemas" not in source

    def test_no_system_clock_fallback(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_no_ai_llm(self):
        import inspect

        source = inspect.getsource(TaskRepository).lower()
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in source

    def test_no_external_network_calls(self):
        import inspect

        source = inspect.getsource(TaskRepository).lower()
        assert "urllib" not in source
        assert "httpx" not in source
        assert "requests" not in source
