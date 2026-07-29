from __future__ import annotations

import importlib
import inspect
from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from app.core.task_exceptions import (
    InvalidTaskError,
    TaskAlreadyCompletedError,
    TaskNotCompletedError,
)
from app.core.tasks import (
    MAX_TASK_DESCRIPTION_LENGTH,
    MAX_TASK_TITLE_LENGTH,
    MIN_TASK_TITLE_LENGTH,
    Task,
    TaskPriority,
    TaskStatus,
    complete_task,
    create_task,
    order_tasks,
    reopen_task,
)

MODULE = "app.core.tasks"

_TZ = UTC


# ===========================================================================
# Helpers
# ===========================================================================


def _uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def _uuid2() -> UUID:
    return UUID("87654321-4321-8765-4321-876543218765")


def _uuid3() -> UUID:
    return UUID("11111111-2222-3333-4444-555555555555")


def _naive_dt() -> datetime:
    return datetime(2025, 6, 15, 12, 30, 0)


def _tz_dt() -> datetime:
    return datetime(2025, 6, 15, 12, 30, 0, tzinfo=_TZ)


def _task(
    *,
    task_id: UUID | None = None,
    title: str = "Buy groceries",
    description: str | None = "Milk and eggs",
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.PENDING,
    due_date: date | None = None,
    completed_at: datetime | None = None,
) -> Task:
    return Task(
        task_id=task_id or _uuid(),
        title=title,
        description=description,
        priority=priority,
        status=status,
        due_date=due_date,
        completed_at=completed_at,
    )


def _source() -> str:
    mod = importlib.import_module(MODULE)
    return inspect.getsource(mod)


# ===========================================================================
# A. Constants
# ===========================================================================


class TestConstants:
    def test_min_title_length(self):
        assert MIN_TASK_TITLE_LENGTH == 1

    def test_max_title_length(self):
        assert MAX_TASK_TITLE_LENGTH == 200

    def test_max_description_length(self):
        assert MAX_TASK_DESCRIPTION_LENGTH == 2000

    def test_all_are_int(self):
        assert isinstance(MIN_TASK_TITLE_LENGTH, int)
        assert isinstance(MAX_TASK_TITLE_LENGTH, int)
        assert isinstance(MAX_TASK_DESCRIPTION_LENGTH, int)

    def test_bounds_sane(self):
        assert MIN_TASK_TITLE_LENGTH <= MAX_TASK_TITLE_LENGTH
        assert MAX_TASK_TITLE_LENGTH < MAX_TASK_DESCRIPTION_LENGTH


# ===========================================================================
# B. Enums
# ===========================================================================


class TestEnums:
    def test_priority_members(self):
        assert {e.name for e in TaskPriority} == {"LOW", "MEDIUM", "HIGH"}

    def test_priority_values(self):
        assert {e.value for e in TaskPriority} == {"low", "medium", "high"}

    def test_priority_no_extra(self):
        assert len(TaskPriority) == 3

    def test_priority_is_str_enum(self):
        assert issubclass(TaskPriority, str)
        assert str(TaskPriority.HIGH) == "high"

    def test_status_members(self):
        assert {e.name for e in TaskStatus} == {"PENDING", "COMPLETED"}

    def test_status_values(self):
        assert {e.value for e in TaskStatus} == {"pending", "completed"}

    def test_status_no_extra(self):
        assert len(TaskStatus) == 2

    def test_status_is_str_enum(self):
        assert issubclass(TaskStatus, str)
        assert str(TaskStatus.PENDING) == "pending"

    def test_priority_not_numeric(self):
        for member in TaskPriority:
            assert not isinstance(member.value, int)


# ===========================================================================
# C. Task dataclass
# ===========================================================================


class TestTaskStructure:
    def test_is_dataclass(self):
        assert hasattr(Task, "__dataclass_fields__")

    def test_frozen(self):
        t = _task()
        with pytest.raises(FrozenInstanceError):
            t.title = "changed"  # type: ignore[misc]

    def test_slotted(self):
        t = _task()
        with pytest.raises((AttributeError, TypeError)):
            t.new_field = "value"  # type: ignore[attr-defined]

    def test_no_dynamic_attributes(self):
        t = _task()
        with pytest.raises((AttributeError, TypeError)):
            t.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_field_order(self):
        fields = list(Task.__dataclass_fields__.keys())
        assert fields == [
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
        ]


    def test_equality(self):
        assert _task() == _task()

    def test_inequality(self):
        assert _task(task_id=_uuid()) != _task(task_id=_uuid2())

    def test_hashable(self):
        assert hash(_task()) == hash(_task())
        assert {_task(), _task()} == {_task()}


# ===========================================================================
# D. Direct construction
# ===========================================================================


class TestDirectConstructionValid:
    def test_pending(self):
        t = Task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
        )
        assert t.status is TaskStatus.PENDING
        assert t.completed_at is None

    def test_completed(self):
        t = Task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED,
            due_date=None,
            completed_at=_naive_dt(),
        )
        assert t.status is TaskStatus.COMPLETED
        assert t.completed_at == _naive_dt()

    def test_none_description(self):
        t = _task(description=None)
        assert t.description is None

    def test_none_due_date(self):
        t = _task(due_date=None)
        assert t.due_date is None

    def test_past_due_date(self):
        t = _task(due_date=date(2020, 1, 1))
        assert t.due_date == date(2020, 1, 1)

    def test_future_due_date(self):
        t = _task(due_date=date(2030, 12, 31))
        assert t.due_date == date(2030, 12, 31)

    def test_naive_datetime(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        assert t.completed_at == _naive_dt()
        assert t.completed_at.tzinfo is None

    def test_timezone_aware_datetime(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_tz_dt())
        assert t.completed_at == _tz_dt()
        assert t.completed_at.tzinfo == _TZ


class TestDirectConstructionInvalid:
    def test_invalid_task_id_none(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=None,  # type: ignore[arg-type]
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_task_id_string(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=str(_uuid()),  # type: ignore[arg-type]
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_task_id_int(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=123,  # type: ignore[arg-type]
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_task_id_bool(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=True,  # type: ignore[arg-type]
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_task_id_float(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=1.5,  # type: ignore[arg-type]
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_title_none(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title=None,  # type: ignore[arg-type]
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_title_int(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title=123,  # type: ignore[arg-type]
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_empty_title(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_whitespace_only_title(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="   ",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_too_long_title(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="x" * (MAX_TASK_TITLE_LENGTH + 1),
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_null_byte_title(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="bad\0title",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_control_char_title(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="bad\ttitle",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_description_int(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description=123,  # type: ignore[arg-type]
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_too_long_description(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description="x" * (MAX_TASK_DESCRIPTION_LENGTH + 1),
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_priority_string(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority="high",  # type: ignore[arg-type]
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
            )

    def test_invalid_status_string(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status="pending",  # type: ignore[arg-type]
                due_date=None,
                completed_at=None,
            )

    def test_datetime_as_due_date(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=datetime(2025, 6, 15),  # type: ignore[arg-type]
                completed_at=None,
            )

    def test_pending_with_completed_at(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=_naive_dt(),
            )

    def test_completed_without_completed_at(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.COMPLETED,
                due_date=None,
                completed_at=None,
            )


# ===========================================================================
# E. create_task()
# ===========================================================================


class TestCreateTask:
    def test_returns_task(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.HIGH,
            due_date=None,
        )
        assert isinstance(t, Task)

    def test_pending_status(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.HIGH,
            due_date=None,
        )
        assert t.status is TaskStatus.PENDING

    def test_completed_at_none(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.HIGH,
            due_date=None,
        )
        assert t.completed_at is None

    def test_title_stripped(self):
        t = create_task(
            task_id=_uuid(),
            title="  Spaced title  ",
            description=None,
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.title == "Spaced title"

    def test_internal_spaces_preserved(self):
        t = create_task(
            task_id=_uuid(),
            title="Buy  two  apples",
            description=None,
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.title == "Buy  two  apples"

    def test_case_preserved(self):
        t = create_task(
            task_id=_uuid(),
            title="Buy MILK",
            description=None,
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.title == "Buy MILK"

    def test_description_stripped(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description="  some description  ",
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.description == "some description"

    def test_empty_description_becomes_none(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description="   ",
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.description is None

    def test_none_description_preserved(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.description is None

    def test_internal_line_breaks_preserved(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description="Line one\nLine two",
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert t.description == "Line one\nLine two"

    def test_past_due_date_accepted(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            due_date=date(2020, 1, 1),
        )
        assert t.due_date == date(2020, 1, 1)

    def test_current_due_date_accepted(self):
        today = date(2025, 6, 15)
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            due_date=today,
        )
        assert t.due_date == today

    def test_future_due_date_accepted(self):
        t = create_task(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            due_date=date(2030, 12, 31),
        )
        assert t.due_date == date(2030, 12, 31)

    def test_input_not_mutated(self):
        title = "  Title  "
        desc = "  Desc  "
        create_task(
            task_id=_uuid(),
            title=title,
            description=desc,
            priority=TaskPriority.LOW,
            due_date=None,
        )
        assert title == "  Title  "
        assert desc == "  Desc  "

    def test_invalid_title_rejected(self):
        with pytest.raises(InvalidTaskError):
            create_task(
                task_id=_uuid(),
                title="",
                description=None,
                priority=TaskPriority.LOW,
                due_date=None,
            )

    def test_invalid_priority_rejected(self):
        with pytest.raises(InvalidTaskError):
            create_task(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority="high",  # type: ignore[arg-type]
                due_date=None,
            )


# ===========================================================================
# F. complete_task()
# ===========================================================================


class TestCompleteTask:
    def test_returns_new_object(self):
        t = _task()
        completed = complete_task(task=t, completed_at=_naive_dt())
        assert completed is not t

    def test_original_unchanged(self):
        t = _task()
        complete_task(task=t, completed_at=_naive_dt())
        assert t.status is TaskStatus.PENDING
        assert t.completed_at is None

    def test_status_completed(self):
        completed = complete_task(task=_task(), completed_at=_naive_dt())
        assert completed.status is TaskStatus.COMPLETED

    def test_exact_completed_at(self):
        ts = _naive_dt()
        completed = complete_task(task=_task(), completed_at=ts)
        assert completed.completed_at is ts
        assert completed.completed_at == ts

    def test_naive_datetime_preserved(self):
        completed = complete_task(task=_task(), completed_at=_naive_dt())
        assert completed.completed_at.tzinfo is None

    def test_timezone_aware_datetime_preserved(self):
        completed = complete_task(task=_task(), completed_at=_tz_dt())
        assert completed.completed_at == _tz_dt()
        assert completed.completed_at.tzinfo == _TZ

    def test_other_fields_preserved(self):
        original = _task(
            title="Task A",
            description="Desc",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
        )
        completed = complete_task(task=original, completed_at=_naive_dt())
        assert completed.task_id == original.task_id
        assert completed.title == "Task A"
        assert completed.description == "Desc"
        assert completed.priority is TaskPriority.HIGH
        assert completed.due_date == date(2025, 7, 1)

    def test_already_completed_raises(self):
        completed_original = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        with pytest.raises(TaskAlreadyCompletedError):
            complete_task(task=completed_original, completed_at=_tz_dt())

    def test_invalid_task_input(self):
        with pytest.raises(InvalidTaskError):
            complete_task(task="not a task", completed_at=_naive_dt())  # type: ignore[arg-type]

    def test_invalid_completed_at_input(self):
        with pytest.raises(InvalidTaskError):
            complete_task(task=_task(), completed_at="2025-06-15")  # type: ignore[arg-type]

    def test_deterministic(self):
        t = _task()
        ts = _naive_dt()
        assert complete_task(task=t, completed_at=ts) == complete_task(task=t, completed_at=ts)


# ===========================================================================
# G. reopen_task()
# ===========================================================================


class TestReopenTask:
    def test_returns_new_object(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        reopened = reopen_task(task=t)
        assert reopened is not t

    def test_original_unchanged(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        reopen_task(task=t)
        assert t.status is TaskStatus.COMPLETED
        assert t.completed_at == _naive_dt()

    def test_status_pending(self):
        reopened = reopen_task(task=_task(status=TaskStatus.COMPLETED, completed_at=_naive_dt()))
        assert reopened.status is TaskStatus.PENDING

    def test_completed_at_none(self):
        reopened = reopen_task(task=_task(status=TaskStatus.COMPLETED, completed_at=_naive_dt()))
        assert reopened.completed_at is None

    def test_other_fields_preserved(self):
        original = _task(
            title="Task A",
            description="Desc",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
            status=TaskStatus.COMPLETED,
            completed_at=_naive_dt(),
        )
        reopened = reopen_task(task=original)
        assert reopened.task_id == original.task_id
        assert reopened.title == "Task A"
        assert reopened.description == "Desc"
        assert reopened.priority is TaskPriority.HIGH
        assert reopened.due_date == date(2025, 7, 1)

    def test_pending_task_raises(self):
        with pytest.raises(TaskNotCompletedError):
            reopen_task(task=_task())

    def test_invalid_task_input(self):
        with pytest.raises(InvalidTaskError):
            reopen_task(task="not a task")  # type: ignore[arg-type]

    def test_deterministic(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        assert reopen_task(task=t) == reopen_task(task=t)


# ===========================================================================
# H. order_tasks()
# ===========================================================================


class TestOrderTasks:
    def test_empty_iterable(self):
        assert order_tasks(tasks=[]) == ()

    def test_one_task(self):
        t = _task()
        assert order_tasks(tasks=[t]) == (t,)

    def test_tuple_input(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        assert order_tasks(tasks=(t2, t1)) == (t1, t2)

    def test_list_input(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        assert order_tasks(tasks=[t2, t1]) == (t1, t2)

    def test_generator_input(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())

        def _gen():
            yield t2
            yield t1

        assert order_tasks(tasks=_gen()) == (t1, t2)

    def test_iterator_input(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        assert order_tasks(tasks=iter([t2, t1])) == (t1, t2)

    def test_materialized_once(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        calls = {"n": 0}

        def _gen():
            calls["n"] += 1
            yield t2
            calls["n"] += 1
            yield t1

        order_tasks(tasks=_gen())
        assert calls["n"] == 2

    def test_returns_tuple(self):
        result = order_tasks(tasks=[_task()])
        assert isinstance(result, tuple)
        assert result is not tuple([_task()])

    def test_input_collection_unchanged(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        original = [t2, t1]
        original_copy = list(original)
        order_tasks(tasks=original)
        assert original == original_copy

    def test_invalid_item_rejected(self):
        with pytest.raises(InvalidTaskError):
            order_tasks(tasks=[_task(), "invalid"])  # type: ignore[list-item]

    def test_pending_before_completed(self):
        pending = _task(task_id=_uuid(), status=TaskStatus.PENDING)
        completed = _task(task_id=_uuid2(), status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        result = order_tasks(tasks=[completed, pending])
        assert result == (pending, completed)

    def test_due_date_before_undated(self):
        undated = _task(task_id=_uuid(), due_date=None)
        dated = _task(task_id=_uuid2(), due_date=date(2030, 1, 1))
        result = order_tasks(tasks=[undated, dated])
        assert result == (dated, undated)

    def test_earlier_due_before_later(self):
        later = _task(task_id=_uuid(), due_date=date(2025, 12, 1))
        earlier = _task(task_id=_uuid2(), due_date=date(2025, 1, 1))
        result = order_tasks(tasks=[later, earlier])
        assert result == (earlier, later)

    def test_high_before_medium_before_low(self):
        low = _task(task_id=_uuid(), priority=TaskPriority.LOW)
        medium = _task(task_id=_uuid2(), priority=TaskPriority.MEDIUM)
        high = _task(task_id=_uuid3(), priority=TaskPriority.HIGH)
        result = order_tasks(tasks=[low, medium, high])
        assert result == (high, medium, low)

    def test_casefolded_title_ordering(self):
        a = _task(task_id=_uuid(), title="banana")
        b = _task(task_id=_uuid2(), title="Apple")
        result = order_tasks(tasks=[a, b])
        assert result == (b, a)

    def test_uuid_tie_breaker(self):
        t1 = _task(task_id=_uuid(), title="Same", due_date=None, priority=TaskPriority.MEDIUM)
        t2 = _task(task_id=_uuid2(), title="Same", due_date=None, priority=TaskPriority.MEDIUM)
        t3 = _task(task_id=_uuid3(), title="Same", due_date=None, priority=TaskPriority.MEDIUM)
        # UUIDs compare by integer value: 1111... < 1234... < 8765...
        result = order_tasks(tasks=[t3, t2, t1])
        assert result == (t3, t1, t2)

    def test_same_input_deterministic(self):
        tasks = [
            _task(task_id=_uuid(), title="B", priority=TaskPriority.LOW),
            _task(task_id=_uuid2(), title="A", priority=TaskPriority.HIGH),
            _task(task_id=_uuid3(), title="C", priority=TaskPriority.MEDIUM),
        ]
        r1 = order_tasks(tasks=list(tasks))
        r2 = order_tasks(tasks=list(tasks))
        assert r1 == r2

    def test_unordered_input_deterministic(self):
        tasks = [
            _task(task_id=_uuid(), title="B", due_date=date(2025, 5, 1)),
            _task(task_id=_uuid2(), title="A", due_date=date(2025, 1, 1)),
            _task(
                task_id=_uuid3(),
                title="C",
                due_date=date(2025, 9, 1),
                status=TaskStatus.COMPLETED,
                completed_at=_naive_dt(),
            ),
        ]
        result = order_tasks(tasks=list(tasks))
        # pending first, then by date
        assert result[0].task_id == _uuid2()
        assert result[1].task_id == _uuid()
        assert result[2].task_id == _uuid3()


# ===========================================================================
# I. Architecture / purity
# ===========================================================================


class TestDomainPurity:
    def test_no_fastapi_import(self):
        assert "fastapi" not in _source().lower()

    def test_no_starlette_import(self):
        assert "starlette" not in _source().lower()

    def test_no_pydantic_import(self):
        assert "pydantic" not in _source().lower()

    def test_no_sqlalchemy_import(self):
        assert "sqlalchemy" not in _source().lower()

    def test_no_alembic_import(self):
        assert "alembic" not in _source().lower()

    def test_no_http_exception(self):
        assert "httpexception" not in _source().lower()

    def test_no_database_import(self):
        assert "from app.db" not in _source()
        assert "import app.db" not in _source()

    def test_no_repository_import(self):
        assert "repositories" not in _source()

    def test_no_service_import(self):
        assert "from app.services" not in _source()

    def test_no_api_import(self):
        assert "from app.api" not in _source()
        assert "import app.api" not in _source()

    def test_no_environment_access(self):
        assert "os.environ" not in _source()
        assert "getenv" not in _source()

    def test_no_network_access(self):
        assert "import request" not in _source().lower()
        assert "urllib" not in _source().lower()
        assert "httpx" not in _source().lower()

    def test_no_system_clock(self):
        assert "date.today(" not in _source()
        assert "datetime.now(" not in _source()
        assert "datetime.utcnow(" not in _source()

    def test_no_random(self):
        assert "random" not in _source().lower()

    def test_no_ai_llm(self):
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in _source().lower()

    def test_only_domain_and_stdlib_imports(self):
        allowed = (
            "from __future__",
            "from collections.abc",
            "from dataclasses",
            "from datetime",
            "from enum",
            "from types",
            "from typing",
            "from uuid",
            "from app.core.task_exceptions",
        )
        lines = [
            ln
            for ln in _source().splitlines()
            if ln.strip().startswith("import ") or ln.strip().startswith("from ")
        ]
        for ln in lines:
            assert any(ln.strip().startswith(a) for a in allowed), f"unexpected import: {ln!r}"


# ===========================================================================
# J. Phase boundaries
# ===========================================================================


class TestPhaseBoundaries:
    def test_task_schema_module_exists(self):
        import importlib

        mod = importlib.import_module("app.schemas.tasks")
        for name in (
            "TaskCreate",
            "TaskData",
            "TaskListData",
            "TaskSuccessResponse",
            "TaskListSuccessResponse",
            "TaskDeleteSuccessResponse",
            "TaskCompletionSuccessResponse",
            "TaskReopenSuccessResponse",
        ):
            assert hasattr(mod, name), f"Missing task schema export: {name}"
        from app.schemas import (
            TaskCompletionSuccessResponse,
            TaskCreate,
            TaskData,
            TaskDeleteSuccessResponse,
            TaskListData,
            TaskListSuccessResponse,
            TaskReopenSuccessResponse,
            TaskSuccessResponse,
        )

        assert TaskCreate is not None
        assert TaskData is not None
        assert TaskListData is not None
        assert TaskSuccessResponse is not None
        assert TaskListSuccessResponse is not None
        assert TaskDeleteSuccessResponse is not None
        assert TaskCompletionSuccessResponse is not None
        assert TaskReopenSuccessResponse is not None

    def test_task_orm_model_exists(self):
        import os

        from app.models.task import Task

        assert os.path.exists("app/models/task.py")
        assert Task is not None

    def test_task_repository_exists(self):
        import os

        assert os.path.exists("app/repositories/task.py")

    def test_task_service_exists(self):
        import os

        assert os.path.exists("app/services/task.py")

    def test_task_api_router_exists(self):
        import os

        assert os.path.exists("app/api/v1/tasks.py")

    def test_task_migration_exists(self):
        import os

        migration_dir = "alembic/versions"
        files = [f for f in os.listdir(migration_dir) if f.endswith(".py") and f != "__init__.py"]
        assert len(files) == 7
        assert any("0295723946b2" in f for f in files)

    def test_task_routes_in_openapi(self):
        from app.main import create_app

        paths = create_app().openapi().get("paths", {})
        task_paths = [p for p in paths if "task" in p.lower()]
        assert "/api/v1/tasks" in task_paths
        assert "/api/v1/tasks/{task_id}" in task_paths
        assert "/api/v1/tasks/{task_id}/complete" in task_paths
        assert "/api/v1/tasks/{task_id}/reopen" in task_paths

    def test_orm_metadata_unchanged(self):
        from app.db.base import Base

        assert set(Base.metadata.tables.keys()) == {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }

    def test_migration_head_unchanged(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(Config("alembic.ini"))
        assert script.get_current_head() == "0295723946b2"

    def test_exactly_one_bearer_auth(self):
        from app.main import create_app

        schemes = create_app().openapi().get("components", {}).get("securitySchemes", {})
        bearer = [v for v in schemes.values() if v.get("scheme") == "bearer"]
        assert len(bearer) == 1
