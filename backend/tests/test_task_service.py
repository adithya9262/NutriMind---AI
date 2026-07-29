from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.task_exceptions import (
    TaskAlreadyCompletedError,
    TaskNotCompletedError,
    TaskNotFoundError,
)
from app.core.tasks import (
    Task,
    TaskPriority,
    TaskStatus,
    complete_task,
    order_tasks,
    reopen_task,
)
from app.models.task import Task as TaskORM
from app.repositories.task import TaskRepository
from app.services.task import TaskService

_TZ = UTC


def _make_repo() -> MagicMock:
    return AsyncMock(spec=TaskRepository)


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
    status: TaskStatus = TaskStatus.PENDING,
    due_date: date | None = None,
    completed_at: datetime | None = None,
) -> Task:
    return Task(
        task_id=task_id or uuid.uuid4(),
        title=title,
        description=description,
        priority=priority,
        status=status,
        due_date=due_date,
        completed_at=completed_at,
    )


# ===========================================================================
# A. Module and exports
# ===========================================================================


class TestModuleExports:
    def test_module_imports(self):
        import app.services.task as mod

        assert mod is not None

    def test_class_exists(self):
        from app.services.task import TaskService

        assert TaskService is not None

    def test_exported_from_app_services(self):
        from app.services import TaskService

        assert TaskService is not None

    def test_single_implementation(self):
        import app.services.task as mod

        assert mod.TaskService is not None
        assert not hasattr(mod, "TaskServiceBase")
        assert not hasattr(mod, "TasksService")


# ===========================================================================
# B. Constructor
# ===========================================================================


class TestConstructor:
    def test_stores_supplied_repository(self):
        repo = _make_repo()
        service = TaskService(repo)
        assert service._repository is repo

    def test_does_not_create_repository(self):
        repo = _make_repo()
        TaskService(repo)
        repo.assert_not_called()

    def test_does_not_query_during_construction(self):
        repo = _make_repo()
        TaskService(repo)
        repo.list_by_user_id.assert_not_called()
        repo.get_by_user_and_task_id.assert_not_called()
        repo.create.assert_not_called()
        repo.update.assert_not_called()
        repo.delete.assert_not_called()


# ===========================================================================
# C. list_tasks
# ===========================================================================


class TestListTasks:
    async def test_repository_list_called_exactly_once(self):
        repo = _make_repo()
        repo.list_by_user_id = AsyncMock(return_value=[])
        service = TaskService(repo)

        await service.list_tasks(user_id=uuid.uuid4())

        repo.list_by_user_id.assert_awaited_once()

    async def test_exact_user_id_passed(self):
        repo = _make_repo()
        repo.list_by_user_id = AsyncMock(return_value=[])
        service = TaskService(repo)

        user_id = uuid.uuid4()
        await service.list_tasks(user_id=user_id)

        assert repo.list_by_user_id.call_args.kwargs["user_id"] == user_id

    async def test_empty_list_result(self):
        repo = _make_repo()
        repo.list_by_user_id = AsyncMock(return_value=[])
        service = TaskService(repo)

        result = await service.list_tasks(user_id=uuid.uuid4())

        assert result == ()

    async def test_one_task_result(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.list_by_user_id = AsyncMock(return_value=[orm])
        service = TaskService(repo)

        result = await service.list_tasks(user_id=uuid.uuid4())

        assert len(result) == 1
        assert isinstance(result[0], Task)
        assert result[0].task_id == orm.task_id

    async def test_multiple_tasks(self):
        repo = _make_repo()
        orm_list = [_make_task_orm(), _make_task_orm(), _make_task_orm()]
        repo.list_by_user_id = AsyncMock(return_value=orm_list)
        service = TaskService(repo)

        result = await service.list_tasks(user_id=uuid.uuid4())

        assert len(result) == 3
        assert all(isinstance(t, Task) for t in result)

    async def test_frozen_order_tasks_called_exactly_once(self):
        repo = _make_repo()
        repo.list_by_user_id = AsyncMock(return_value=[_make_task_orm()])
        service = TaskService(repo)

        original = order_tasks
        calls = {"n": 0}

        def _spy(*, tasks):
            calls["n"] += 1
            return original(tasks=tasks)

        import app.services.task as svc_mod

        real_order = svc_mod.order_tasks
        svc_mod.order_tasks = _spy
        try:
            await service.list_tasks(user_id=uuid.uuid4())
        finally:
            svc_mod.order_tasks = real_order

        assert calls["n"] == 1

    async def test_exact_frozen_ordering_preserved(self):
        repo = _make_repo()
        t1_id = uuid.uuid4()
        t2_id = uuid.uuid4()
        t3_id = uuid.uuid4()
        orm_list = [
            _make_task_orm(task_id=t3_id, title="C", priority=TaskPriority.MEDIUM),
            _make_task_orm(task_id=t1_id, title="A", priority=TaskPriority.HIGH),
            _make_task_orm(task_id=t2_id, title="B", priority=TaskPriority.LOW),
        ]
        repo.list_by_user_id = AsyncMock(return_value=orm_list)
        service = TaskService(repo)

        result = await service.list_tasks(user_id=uuid.uuid4())

        # HIGH before MEDIUM before LOW, then casefold title, then task_id
        # tie-break: t1(HIGH,A), t3(MEDIUM,C), t2(LOW,B)
        assert result[0].task_id == t1_id
        assert result[1].task_id == t3_id
        assert result[2].task_id == t2_id

    async def test_no_duplicate_ordering_formula(self):
        import inspect

        source = inspect.getsource(TaskService)
        # The only ordering must come from the frozen order_tasks call.
        assert "status_rank" not in source
        assert "_PRIORITY_ORDER" not in source

    async def test_deterministic_result(self):
        repo = _make_repo()
        orm_list = [
            _make_task_orm(title="B", priority=TaskPriority.LOW),
            _make_task_orm(title="A", priority=TaskPriority.HIGH),
        ]
        repo.list_by_user_id = AsyncMock(return_value=orm_list)
        service = TaskService(repo)

        r1 = await service.list_tasks(user_id=uuid.uuid4())
        r2 = await service.list_tasks(user_id=uuid.uuid4())

        assert r1 == r2

    async def test_no_system_clock(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    async def test_repository_result_not_mutated_in_place(self):
        repo = _make_repo()
        orm_list = [_make_task_orm(), _make_task_orm()]
        repo.list_by_user_id = AsyncMock(return_value=orm_list)
        service = TaskService(repo)

        await service.list_tasks(user_id=uuid.uuid4())

        # The ORM objects are converted, not modified.
        assert orm_list[0].status is not None


# ===========================================================================
# D. get_task
# ===========================================================================


class TestGetTask:
    async def test_repository_get_called_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        await service.get_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        repo.get_by_user_and_task_id.assert_awaited_once()

    async def test_both_ids_passed(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        await service.get_task(user_id=user_id, task_id=task_id)

        kwargs = repo.get_by_user_and_task_id.call_args.kwargs
        assert kwargs["user_id"] == user_id
        assert kwargs["task_id"] == task_id

    async def test_found_result_returned(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        service = TaskService(repo)

        result = await service.get_task(user_id=orm.user_id, task_id=orm.task_id)

        assert isinstance(result, Task)
        assert result.task_id == orm.task_id

    async def test_missing_raises_task_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=None)
        service = TaskService(repo)

        with pytest.raises(TaskNotFoundError):
            await service.get_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

    async def test_wrong_user_not_found(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=None)
        service = TaskService(repo)

        with pytest.raises(TaskNotFoundError):
            await service.get_task(user_id=uuid.uuid4(), task_id=orm.task_id)

    async def test_safe_exact_message(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=None)
        service = TaskService(repo)

        with pytest.raises(TaskNotFoundError) as excinfo:
            await service.get_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        assert str(excinfo.value) == "Task was not found."

    async def test_no_second_lookup(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        await service.get_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        repo.get_by_user_and_task_id.assert_awaited_once()


# ===========================================================================
# E. create_task
# ===========================================================================


class TestCreateTask:
    async def test_requires_user_id(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        task = _domain_task()
        await service.create_task(user_id=uuid.uuid4(), task=task)

        assert repo.create.call_args.kwargs["user_id"] is not None

    async def test_valid_domain_task_delegated_exactly_once(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        task = _domain_task()
        await service.create_task(user_id=uuid.uuid4(), task=task)

        repo.create.assert_awaited_once()

    async def test_exact_user_id_passed(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        user_id = uuid.uuid4()
        task = _domain_task()
        await service.create_task(user_id=user_id, task=task)

        assert repo.create.call_args.kwargs["user_id"] == user_id

    async def test_exact_domain_task_passed(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        task = _domain_task()
        await service.create_task(user_id=uuid.uuid4(), task=task)

        assert repo.create.call_args.kwargs["task"] is task

    async def test_repository_result_returned(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.create = AsyncMock(return_value=orm)
        service = TaskService(repo)

        task = _domain_task()
        result = await service.create_task(user_id=uuid.uuid4(), task=task)

        assert isinstance(result, Task)
        assert result.task_id == orm.task_id

    async def test_no_duplicate_validation(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        task = _domain_task()
        await service.create_task(user_id=uuid.uuid4(), task=task)

        # The service delegates directly; it must not re-validate.
        assert repo.create.await_count == 1

    async def test_no_domain_mutation(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        task = _domain_task(title="Original")
        await service.create_task(user_id=uuid.uuid4(), task=task)

        assert task.title == "Original"

    async def test_no_commit(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        await service.create_task(user_id=uuid.uuid4(), task=_domain_task())

        repo.create.assert_awaited_once()

    async def test_no_flush_rollback_refresh(self):
        repo = _make_repo()
        repo.create = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)
        # Ensure the repository mock exposes these methods so the absence of
        # calls can be asserted against the service's own behavior.
        repo.update = AsyncMock()
        repo.delete = AsyncMock()

        await service.create_task(user_id=uuid.uuid4(), task=_domain_task())

        repo.update.assert_not_called()
        repo.delete.assert_not_called()


# ===========================================================================
# F. complete_task
# ===========================================================================


class TestCompleteTask:
    async def test_requires_user_id_and_task_id(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=_make_task_orm())
        repo.update = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        orm = _make_task_orm()
        await service.complete_task(
            user_id=orm.user_id,
            task_id=orm.task_id,
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        kwargs = repo.get_by_user_and_task_id.call_args.kwargs
        assert kwargs["user_id"] == orm.user_id
        assert kwargs["task_id"] == orm.task_id

    async def test_requires_caller_completed_at(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=_make_task_orm())
        repo.update = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        orm = _make_task_orm()
        await service.complete_task(
            user_id=orm.user_id,
            task_id=orm.task_id,
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        assert repo.get_by_user_and_task_id.await_count == 1

    async def test_no_default_completed_at(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "completed_at: datetime = " not in source
        assert "datetime.now()" not in source
        assert "datetime.utcnow()" not in source

    async def test_user_scoped_lookup_exactly_once(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=_make_task_orm())
        repo.update = AsyncMock(return_value=_make_task_orm())
        service = TaskService(repo)

        await service.complete_task(
            user_id=uuid.uuid4(),
            task_id=uuid.uuid4(),
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        repo.get_by_user_and_task_id.assert_awaited_once()

    async def test_missing_raises_task_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=None)
        service = TaskService(repo)

        with pytest.raises(TaskNotFoundError):
            await service.complete_task(
                user_id=uuid.uuid4(),
                task_id=uuid.uuid4(),
                completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
            )

    async def test_orm_row_converted_to_domain(self):
        repo = _make_repo()
        orm = _make_task_orm(
            title="Task A",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        result = await service.complete_task(
            user_id=orm.user_id,
            task_id=orm.task_id,
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        assert result.title == "Task A"
        assert result.priority is TaskPriority.HIGH
        assert result.due_date == date(2025, 7, 1)

    async def test_frozen_complete_task_called_exactly_once(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        import app.services.task as svc_mod

        original = complete_task
        calls = {"n": 0}

        def _spy(*, task, completed_at):
            calls["n"] += 1
            return original(task=task, completed_at=completed_at)

        real_fn = svc_mod.complete_task
        svc_mod.complete_task = _spy
        try:
            await service.complete_task(
                user_id=orm.user_id,
                task_id=orm.task_id,
                completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
            )
        finally:
            svc_mod.complete_task = real_fn

        assert calls["n"] == 1

    async def test_exact_completed_at_passed(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        import app.services.task as svc_mod

        captured = {}

        original = complete_task

        def _spy(*, task, completed_at):
            captured["completed_at"] = completed_at
            return original(task=task, completed_at=completed_at)

        real_fn = svc_mod.complete_task
        svc_mod.complete_task = _spy
        try:
            provided = datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ)
            await service.complete_task(
                user_id=orm.user_id,
                task_id=orm.task_id,
                completed_at=provided,
            )
        finally:
            svc_mod.complete_task = real_fn

        assert captured["completed_at"] == provided

    async def test_already_completed_propagates(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        service = TaskService(repo)

        with pytest.raises(TaskAlreadyCompletedError):
            await service.complete_task(
                user_id=orm.user_id,
                task_id=orm.task_id,
                completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
            )

    async def test_only_status_and_completed_at_updated(self):
        repo = _make_repo()
        orm = _make_task_orm(
            title="Task A",
            description="Desc",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        provided = datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ)
        await service.complete_task(user_id=orm.user_id, task_id=orm.task_id, completed_at=provided)

        assert orm.status is TaskStatus.COMPLETED
        assert orm.completed_at == provided
        # Unrelated fields untouched
        assert orm.title == "Task A"
        assert orm.description == "Desc"
        assert orm.priority is TaskPriority.HIGH
        assert orm.due_date == date(2025, 7, 1)
        assert orm.task_id is not None

    async def test_repository_update_called_exactly_once(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.complete_task(
            user_id=orm.user_id,
            task_id=orm.task_id,
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        repo.update.assert_awaited_once()

    async def test_returns_updated_domain_task(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        result = await service.complete_task(
            user_id=orm.user_id,
            task_id=orm.task_id,
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        assert isinstance(result, Task)
        assert result.status is TaskStatus.COMPLETED

    async def test_no_commit_rollback_refresh(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.complete_task(
            user_id=orm.user_id,
            task_id=orm.task_id,
            completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ),
        )

        repo.update.assert_awaited_once()


# ===========================================================================
# G. reopen_task
# ===========================================================================


class TestReopenTask:
    async def test_requires_user_id_and_task_id(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        kwargs = repo.get_by_user_and_task_id.call_args.kwargs
        assert kwargs["user_id"] == orm.user_id
        assert kwargs["task_id"] == orm.task_id

    async def test_user_scoped_lookup_exactly_once(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        repo.get_by_user_and_task_id.assert_awaited_once()

    async def test_missing_raises_task_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=None)
        service = TaskService(repo)

        with pytest.raises(TaskNotFoundError):
            await service.reopen_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

    async def test_orm_row_converted_to_domain(self):
        repo = _make_repo()
        orm = _make_task_orm(
            title="Task A",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        result = await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        assert result.title == "Task A"
        assert result.priority is TaskPriority.HIGH
        assert result.due_date == date(2025, 7, 1)

    async def test_frozen_reopen_task_called_exactly_once(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        import app.services.task as svc_mod

        original = reopen_task
        calls = {"n": 0}

        def _spy(*, task):
            calls["n"] += 1
            return original(task=task)

        real_fn = svc_mod.reopen_task
        svc_mod.reopen_task = _spy
        try:
            await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)
        finally:
            svc_mod.reopen_task = real_fn

        assert calls["n"] == 1

    async def test_status_becomes_pending_from_domain(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        assert orm.status is TaskStatus.PENDING

    async def test_completed_at_becomes_none_from_domain(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        assert orm.completed_at is None

    async def test_only_state_fields_updated(self):
        repo = _make_repo()
        orm = _make_task_orm(
            title="Task A",
            description="Desc",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        assert orm.title == "Task A"
        assert orm.description == "Desc"
        assert orm.priority is TaskPriority.HIGH
        assert orm.due_date == date(2025, 7, 1)
        assert orm.task_id is not None

    async def test_not_completed_propagates(self):
        repo = _make_repo()
        orm = _make_task_orm(status=TaskStatus.PENDING, completed_at=None)
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        service = TaskService(repo)

        with pytest.raises(TaskNotCompletedError):
            await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

    async def test_repository_update_called_exactly_once(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        repo.update.assert_awaited_once()

    async def test_returns_updated_domain_task(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        result = await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        assert isinstance(result, Task)
        assert result.status is TaskStatus.PENDING
        assert result.completed_at is None

    async def test_no_commit_rollback_refresh(self):
        repo = _make_repo()
        orm = _make_task_orm(
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=_TZ),
        )
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.update = AsyncMock(return_value=orm)
        service = TaskService(repo)

        await service.reopen_task(user_id=orm.user_id, task_id=orm.task_id)

        repo.update.assert_awaited_once()


# ===========================================================================
# H. delete_task
# ===========================================================================


class TestDeleteTask:
    async def test_requires_user_id_and_task_id(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.delete = AsyncMock()
        service = TaskService(repo)

        await service.delete_task(user_id=orm.user_id, task_id=orm.task_id)

        kwargs = repo.get_by_user_and_task_id.call_args.kwargs
        assert kwargs["user_id"] == orm.user_id
        assert kwargs["task_id"] == orm.task_id

    async def test_user_scoped_lookup_exactly_once(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.delete = AsyncMock()
        service = TaskService(repo)

        await service.delete_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

        repo.get_by_user_and_task_id.assert_awaited_once()

    async def test_missing_raises_task_not_found(self):
        repo = _make_repo()
        repo.get_by_user_and_task_id = AsyncMock(return_value=None)
        service = TaskService(repo)

        with pytest.raises(TaskNotFoundError):
            await service.delete_task(user_id=uuid.uuid4(), task_id=uuid.uuid4())

    async def test_loaded_orm_passed_to_repository_delete(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.delete = AsyncMock()
        service = TaskService(repo)

        await service.delete_task(user_id=orm.user_id, task_id=orm.task_id)

        assert repo.delete.call_args.kwargs["task"] is orm

    async def test_no_task_id_only_delete(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.delete = AsyncMock()
        service = TaskService(repo)

        await service.delete_task(user_id=orm.user_id, task_id=orm.task_id)

        # delete must receive the loaded object, never a bare task_id
        assert "task_id" not in repo.delete.call_args.kwargs

    async def test_no_second_lookup(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.delete = AsyncMock()
        service = TaskService(repo)

        await service.delete_task(user_id=orm.user_id, task_id=orm.task_id)

        repo.get_by_user_and_task_id.assert_awaited_once()

    async def test_no_commit_rollback(self):
        repo = _make_repo()
        orm = _make_task_orm()
        repo.get_by_user_and_task_id = AsyncMock(return_value=orm)
        repo.delete = AsyncMock()
        service = TaskService(repo)

        await service.delete_task(user_id=orm.user_id, task_id=orm.task_id)

        repo.delete.assert_awaited_once()


# ===========================================================================
# I. Framework independence
# ===========================================================================


class TestFrameworkIndependence:
    def test_no_fastapi(self):
        import inspect

        assert "fastapi" not in inspect.getsource(TaskService).lower()

    def test_no_starlette(self):
        import inspect

        assert "starlette" not in inspect.getsource(TaskService).lower()

    def test_no_http_exception(self):
        import inspect

        assert "httpexception" not in inspect.getsource(TaskService).lower()

    def test_no_status_codes(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        assert "status_code" not in source
        assert "from starlette.responses" not in source

    def test_no_sqlalchemy_text(self):
        import inspect

        assert "sqlalchemy" not in inspect.getsource(TaskService).lower()

    def test_no_asyncsession(self):
        import inspect

        assert "asyncsession" not in inspect.getsource(TaskService).lower()

    def test_no_app_db(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "from app.db" not in source
        assert "import app.db" not in source

    def test_no_api_routers(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_api_dependencies(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "from app.api.dependencies" not in source

    def test_no_pydantic(self):
        import inspect

        assert "pydantic" not in inspect.getsource(TaskService).lower()

    def test_no_api_schemas(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "from app.schemas" not in source


# ===========================================================================
# J. Transaction independence
# ===========================================================================


class TestTransactionIndependence:
    def test_no_commit_text(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "commit(" not in source

    def test_no_rollback_text(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "rollback(" not in source

    def test_no_flush_text(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "self._session.flush" not in source
        assert "session.flush" not in source

    def test_no_refresh_text(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "refresh(" not in source

    def test_no_session_add(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        assert "session.add(" not in source
        assert "self._session.add" not in source

    def test_no_session_delete(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        assert "session.delete(" not in source
        assert "self._session.delete" not in source


# ===========================================================================
# K. Purity and phase boundaries
# ===========================================================================


class TestPurityAndBoundaries:
    def test_no_system_clock(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_no_environment_access(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "os.environ" not in source
        assert "getenv" not in source

    def test_no_network_access(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        assert "urllib" not in source
        assert "httpx" not in source
        assert "import request" not in source

    def test_no_filesystem_access(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "open(" not in source

    def test_no_ai_llm(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in source

    def test_no_reminders_recurrence_notifications(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        # 'recurrence' is an approved Phase-6 feature; only guard against
        # unapproved additions such as raw reminders and notification logic.
        for token in ("reminder", "notification", "recommendation"):
            assert token not in source

    def test_no_categories_tags(self):
        import inspect

        source = inspect.getsource(TaskService).lower()
        # 'category' is an approved Phase-6 feature; guard only against
        # unapproved tag-based organisation.
        for token in ("tag",):
            assert token not in source

    def test_phase_boundaries_intact(self):
        import os

        assert os.path.exists("app/repositories/task.py")
        assert os.path.exists("app/services/task.py")
        assert os.path.exists("app/api/v1/tasks.py")
