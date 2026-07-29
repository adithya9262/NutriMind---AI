from __future__ import annotations

import importlib
import inspect
import json
from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.tasks import (
    MAX_TASK_DESCRIPTION_LENGTH,
    MAX_TASK_TITLE_LENGTH,
    Task,
    TaskPriority,
    TaskStatus,
    TaskCategory,
    TaskRecurrence,
)
from app.schemas.tasks import (
    TaskCompletionSuccessResponse,
    TaskCreate,
    TaskData,
    TaskDeleteSuccessResponse,
    TaskListData,
    TaskListSuccessResponse,
    TaskReopenSuccessResponse,
    TaskSuccessResponse,
)

SCHEMA_MODULE = "app.schemas.tasks"
DOMAIN_MODULE = "app.core.tasks"

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


# ===========================================================================
# A. Module and exports
# ===========================================================================


class TestModuleExports:
    def test_module_imports_successfully(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        assert mod is not None

    def test_exact_public_classes_exist(self):
        mod = importlib.import_module(SCHEMA_MODULE)
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
            assert hasattr(mod, name), f"Missing schema: {name}"

    def test_package_exports_work(self):
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

    def test_all_contains_expected_task_schemas(self):
        from app.schemas import __all__ as exports

        expected = {
            "TaskCreate",
            "TaskData",
            "TaskListData",
            "TaskSuccessResponse",
            "TaskListSuccessResponse",
            "TaskDeleteSuccessResponse",
            "TaskCompletionSuccessResponse",
            "TaskReopenSuccessResponse",
        }
        assert expected.issubset(set(exports))

    def test_no_duplicated_domain_constants_or_types(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "MIN_TASK_TITLE_LENGTH = " not in source
        assert "MAX_TASK_TITLE_LENGTH = " not in source
        assert "MAX_TASK_DESCRIPTION_LENGTH = " not in source
        assert "class TaskPriority" not in source
        assert "class TaskStatus" not in source
        assert "class Task:" not in source


# ===========================================================================
# B. TaskCreate
# ===========================================================================


class TestTaskCreateFieldSet:
    def test_exact_field_names(self):
        fields = set(TaskCreate.model_fields)
        assert fields == {"title", "description", "priority", "due_date", "category", "recurrence"}

    def test_exact_field_order(self):
        order = list(TaskCreate.model_fields.keys())
        assert order == ["title", "description", "priority", "due_date", "category", "recurrence"]

    def test_required_title(self):
        assert TaskCreate.model_fields["title"].is_required()

    def test_default_description_none(self):
        obj = TaskCreate(title="Valid")
        assert obj.description is None

    def test_default_priority_medium(self):
        obj = TaskCreate(title="Valid")
        assert obj.priority is TaskPriority.MEDIUM

    def test_default_due_date_none(self):
        obj = TaskCreate(title="Valid")
        assert obj.due_date is None

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", extra_field="value")  # type: ignore[call-arg]

    def test_valid_minimal_title(self):
        obj = TaskCreate(title="X")
        assert obj.title == "X"

    def test_valid_maximum_title(self):
        obj = TaskCreate(title="x" * MAX_TASK_TITLE_LENGTH)
        assert obj.title == "x" * MAX_TASK_TITLE_LENGTH

    def test_title_stripping(self):
        obj = TaskCreate(title="  Spaced title  ")
        assert obj.title == "Spaced title"

    def test_internal_spaces_preserved(self):
        obj = TaskCreate(title="Buy  two  apples")
        assert obj.title == "Buy  two  apples"

    def test_case_preserved(self):
        obj = TaskCreate(title="Buy MILK")
        assert obj.title == "Buy MILK"

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="")

    def test_whitespace_only_title_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="   ")

    def test_too_long_title_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * (MAX_TASK_TITLE_LENGTH + 1))

    def test_null_byte_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="bad\0title")

    def test_prohibited_control_characters_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="bad\ttitle")

    def test_invalid_title_types_rejected(self):
        for bad in (123, 1.5, True, ["a"], None):
            with pytest.raises(ValidationError):
                TaskCreate(title=bad)  # type: ignore[arg-type]

    def test_description_none(self):
        obj = TaskCreate(title="Valid", description=None)
        assert obj.description is None

    def test_description_stripping(self):
        obj = TaskCreate(title="Valid", description="  some description  ")
        assert obj.description == "some description"

    def test_empty_description_becomes_none(self):
        obj = TaskCreate(title="Valid", description="   ")
        assert obj.description is None

    def test_internal_line_breaks_preserved(self):
        obj = TaskCreate(title="Valid", description="Line one\nLine two")
        assert obj.description == "Line one\nLine two"

    def test_carriage_return_preserved(self):
        obj = TaskCreate(title="Valid", description="Line one\rLine two")
        assert obj.description == "Line one\rLine two"

    def test_maximum_description_accepted(self):
        obj = TaskCreate(title="Valid", description="x" * MAX_TASK_DESCRIPTION_LENGTH)
        assert obj.description == "x" * MAX_TASK_DESCRIPTION_LENGTH

    def test_too_long_description_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", description="x" * (MAX_TASK_DESCRIPTION_LENGTH + 1))

    def test_null_byte_description_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", description="bad\0desc")

    def test_prohibited_control_characters_description_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", description="bad\tdesc")

    def test_invalid_description_types_rejected(self):
        for bad in (123, 1.5, True, ["a"]):
            with pytest.raises(ValidationError):
                TaskCreate(title="Valid", description=bad)  # type: ignore[arg-type]

    def test_low_accepted(self):
        obj = TaskCreate(title="Valid", priority=TaskPriority.LOW)
        assert obj.priority is TaskPriority.LOW

    def test_medium_accepted(self):
        obj = TaskCreate(title="Valid", priority=TaskPriority.MEDIUM)
        assert obj.priority is TaskPriority.MEDIUM

    def test_high_accepted(self):
        obj = TaskCreate(title="Valid", priority=TaskPriority.HIGH)
        assert obj.priority is TaskPriority.HIGH

    def test_lowercase_enum_string_accepted(self):
        obj = TaskCreate(title="Valid", priority="low")  # type: ignore[arg-type]
        assert obj.priority is TaskPriority.LOW

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", priority="urgent")  # type: ignore[arg-type]

    def test_boolean_priority_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", priority=True)  # type: ignore[arg-type]

    def test_past_date_accepted(self):
        obj = TaskCreate(title="Valid", due_date=date(2020, 1, 1))
        assert obj.due_date == date(2020, 1, 1)

    def test_current_explicitly_supplied_date_accepted(self):
        today = date(2025, 6, 15)
        obj = TaskCreate(title="Valid", due_date=today)
        assert obj.due_date == today

    def test_future_date_accepted(self):
        obj = TaskCreate(title="Valid", due_date=date(2030, 12, 31))
        assert obj.due_date == date(2030, 12, 31)

    def test_none_date_accepted(self):
        obj = TaskCreate(title="Valid", due_date=None)
        assert obj.due_date is None

    def test_datetime_rejected(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="Valid", due_date=datetime(2025, 6, 15))  # type: ignore[arg-type]

    def test_no_date_today_used(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_caller_input_not_mutated(self):
        title = "  Title  "
        desc = "  Desc  "
        TaskCreate(title=title, description=desc)
        assert title == "  Title  "
        assert desc == "  Desc  "


# ===========================================================================
# C. TaskData
# ===========================================================================


class TestTaskDataFieldSet:
    def test_exact_nine_fields(self):
        fields = set(TaskData.model_fields)
        assert fields == {
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
        }

    def test_exact_field_order(self):
        order = list(TaskData.model_fields.keys())
        assert order == [
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

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskData(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
                category=TaskCategory.CUSTOM,
                recurrence=TaskRecurrence.NONE,
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_frozen_true(self):
        assert TaskData.model_config.get("frozen") is True

    def test_from_attributes_true(self):
        assert TaskData.model_config.get("from_attributes") is True

    def test_valid_pending_task(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.status is TaskStatus.PENDING
        assert obj.completed_at is None

    def test_valid_completed_task(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED,
            due_date=None,
            completed_at=_naive_dt(),
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.status is TaskStatus.COMPLETED
        assert obj.completed_at == _naive_dt()

    def test_uuid_preserved(self):
        uid = _uuid()
        obj = TaskData(
            task_id=uid,
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.task_id == uid

    def test_date_preserved(self):
        d = date(2025, 7, 1)
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=d,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.due_date == d

    def test_naive_datetime_preserved(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.COMPLETED,
            due_date=None,
            completed_at=_naive_dt(),
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.completed_at == _naive_dt()
        assert obj.completed_at.tzinfo is None

    def test_timezone_aware_datetime_preserved(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.COMPLETED,
            due_date=None,
            completed_at=_tz_dt(),
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.completed_at == _tz_dt()
        assert obj.completed_at.tzinfo == _TZ

    def test_priority_enum_preserved(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.priority is TaskPriority.HIGH

    def test_status_enum_preserved(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.status is TaskStatus.PENDING

    def test_pending_with_completed_at_rejected(self):
        with pytest.raises(ValidationError):
            TaskData(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=_naive_dt(),
                category=TaskCategory.CUSTOM,
                recurrence=TaskRecurrence.NONE,
            )

    def test_completed_without_completed_at_rejected(self):
        with pytest.raises(ValidationError):
            TaskData(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.COMPLETED,
                due_date=None,
                completed_at=None,
                category=TaskCategory.CUSTOM,
                recurrence=TaskRecurrence.NONE,
            )

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValidationError):
            TaskData(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority="urgent",  # type: ignore[arg-type]
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=None,
                category=TaskCategory.CUSTOM,
                recurrence=TaskRecurrence.NONE,
            )

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            TaskData(
                task_id=_uuid(),
                title="Valid",
                description=None,
                priority=TaskPriority.MEDIUM,
                status="open",  # type: ignore[arg-type]
                due_date=None,
                completed_at=None,
                category=TaskCategory.CUSTOM,
                recurrence=TaskRecurrence.NONE,
            )

    def test_lowercase_priority_string_accepted(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority="low",  # type: ignore[arg-type]
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.priority is TaskPriority.LOW

    def test_lowercase_status_string_accepted(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status="pending",  # type: ignore[arg-type]
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        assert obj.status is TaskStatus.PENDING

    def test_top_level_mutation_raises_validation_error(self):
        obj = TaskData(
            task_id=_uuid(),
            title="Valid",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=None,
            completed_at=None,
            category=TaskCategory.CUSTOM,
            recurrence=TaskRecurrence.NONE,
        )
        with pytest.raises(ValidationError):
            obj.title = "changed"  # type: ignore[misc]

    def test_no_user_id_field(self):
        assert "user_id" not in TaskData.model_fields

    def test_no_orm_id_field(self):
        assert "id" not in TaskData.model_fields

    def test_no_created_at(self):
        assert "created_at" not in TaskData.model_fields

    def test_no_updated_at(self):
        assert "updated_at" not in TaskData.model_fields

    def test_no_internal_sqlalchemy_state(self):
        assert "_sa_instance_state" not in TaskData.model_fields


# ===========================================================================
# D. TaskData.from_domain()
# ===========================================================================


class TestTaskDataFromDomain:
    def test_returns_task_data(self):
        data = TaskData.from_domain(_task())
        assert isinstance(data, TaskData)

    def test_copies_all_seven_fields_exactly(self):
        t = _task(
            title="Task A",
            description="Desc",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
        )
        data = TaskData.from_domain(t)
        assert data.task_id == t.task_id
        assert data.title == t.title
        assert data.description == t.description
        assert data.priority is t.priority
        assert data.status is t.status
        assert data.due_date == t.due_date
        assert data.completed_at == t.completed_at

    def test_pending_task_conversion(self):
        t = _task(status=TaskStatus.PENDING, completed_at=None)
        data = TaskData.from_domain(t)
        assert data.status is TaskStatus.PENDING
        assert data.completed_at is None

    def test_completed_task_conversion(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        data = TaskData.from_domain(t)
        assert data.status is TaskStatus.COMPLETED
        assert data.completed_at == _naive_dt()

    def test_none_description_preserved(self):
        data = TaskData.from_domain(_task(description=None))
        assert data.description is None

    def test_none_due_date_preserved(self):
        data = TaskData.from_domain(_task(due_date=None))
        assert data.due_date is None

    def test_naive_datetime_preserved_exactly(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_naive_dt())
        data = TaskData.from_domain(t)
        assert data.completed_at == _naive_dt()
        assert data.completed_at.tzinfo is None

    def test_timezone_aware_datetime_preserved_exactly(self):
        t = _task(status=TaskStatus.COMPLETED, completed_at=_tz_dt())
        data = TaskData.from_domain(t)
        assert data.completed_at == _tz_dt()
        assert data.completed_at.tzinfo == _TZ

    def test_domain_input_not_mutated(self):
        t = _task()
        TaskData.from_domain(t)
        assert t.title == "Buy groceries"
        assert t.status is TaskStatus.PENDING
        assert t.completed_at is None

    def test_deterministic(self):
        t = _task()
        assert TaskData.from_domain(t).model_dump() == TaskData.from_domain(t).model_dump()

    def test_no_status_change(self):
        t = _task(status=TaskStatus.PENDING)
        assert TaskData.from_domain(t).status is TaskStatus.PENDING

    def test_no_priority_change(self):
        t = _task(priority=TaskPriority.HIGH)
        assert TaskData.from_domain(t).priority is TaskPriority.HIGH

    def test_no_date_conversion(self):
        t = _task(due_date=date(2025, 1, 1))
        assert TaskData.from_domain(t).due_date == date(2025, 1, 1)

    def test_no_generated_timestamp(self):
        t = _task(status=TaskStatus.PENDING, completed_at=None)
        assert TaskData.from_domain(t).completed_at is None

    def test_invalid_non_domain_object_rejected(self):
        with pytest.raises(TypeError, match="Task"):
            TaskData.from_domain("not a task")  # type: ignore[arg-type]


# ===========================================================================
# E. TaskListData
# ===========================================================================


class TestTaskListDataFieldSet:
    def test_exact_tasks_field(self):
        fields = set(TaskListData.model_fields)
        assert fields == {"tasks"}

    def test_tasks_required(self):
        assert TaskListData.model_fields["tasks"].is_required()

    def test_tasks_cannot_be_none(self):
        with pytest.raises(ValidationError):
            TaskListData(tasks=None)  # type: ignore[arg-type]

    def test_empty_tuple_accepted(self):
        obj = TaskListData(tasks=())
        assert obj.tasks == ()

    def test_tuple_accepted(self):
        d = TaskData.from_domain(_task())
        obj = TaskListData(tasks=(d,))
        assert len(obj.tasks) == 1

    def test_list_accepted_coerced_to_tuple(self):
        d = TaskData.from_domain(_task())
        obj = TaskListData(tasks=[d])
        assert isinstance(obj.tasks, tuple)
        assert len(obj.tasks) == 1

    def test_nested_values_converted_to_tuple(self):
        obj = TaskListData(tasks=[])
        assert isinstance(obj.tasks, tuple)

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskListData(tasks=(), extra_field="value")  # type: ignore[call-arg]

    def test_frozen_true(self):
        assert TaskListData.model_config.get("frozen") is True

    def test_top_level_mutation_rejected(self):
        obj = TaskListData(tasks=())
        with pytest.raises(ValidationError):
            obj.tasks = (TaskData.from_domain(_task()),)  # type: ignore[misc]

    def test_nested_mutation_rejected(self):
        d = TaskData.from_domain(_task())
        obj = TaskListData(tasks=(d,))
        with pytest.raises(ValidationError):
            obj.tasks[0].title = "changed"  # type: ignore[misc]

    def test_invalid_nested_item_rejected(self):
        with pytest.raises(ValidationError):
            TaskListData(
                tasks=[  # type: ignore[list-item]
                    {
                        "task_id": str(_uuid()),
                        "title": "Valid",
                        "description": None,
                        "priority": "medium",
                        "status": "pending",
                        "due_date": None,
                        "completed_at": None,
                    },
                    "invalid",
                ]
            )

    def test_extra_nested_field_rejected(self):
        with pytest.raises(ValidationError):
            TaskListData(
                tasks=[  # type: ignore[list-item]
                    {
                        "task_id": str(_uuid()),
                        "title": "Valid",
                        "description": None,
                        "priority": "medium",
                        "status": "pending",
                        "due_date": None,
                        "completed_at": None,
                        "extra": "x",
                    }
                ]
            )

    def test_caller_owned_list_not_mutated(self):
        lst = []
        TaskListData(tasks=lst)
        assert lst == []


# ===========================================================================
# F. TaskListData.from_domain()
# ===========================================================================


class TestTaskListDataFromDomain:
    def test_empty_iterable(self):
        result = TaskListData.from_domain([])
        assert result.tasks == ()

    def test_tuple(self):
        result = TaskListData.from_domain((_task(),))
        assert len(result.tasks) == 1

    def test_list(self):
        result = TaskListData.from_domain([_task()])
        assert len(result.tasks) == 1

    def test_generator(self):
        def _gen():
            yield _task()
            yield _task(task_id=_uuid2())

        result = TaskListData.from_domain(_gen())
        assert len(result.tasks) == 2

    def test_iterator(self):
        result = TaskListData.from_domain(iter([_task()]))
        assert len(result.tasks) == 1

    def test_uses_task_data_from_domain_for_every_task(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        result = TaskListData.from_domain([t1, t2])
        assert isinstance(result.tasks[0], TaskData)
        assert isinstance(result.tasks[1], TaskData)
        assert result.tasks[0].task_id == t1.task_id
        assert result.tasks[1].task_id == t2.task_id

    def test_preserves_input_order(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        t3 = _task(task_id=_uuid3())
        result = TaskListData.from_domain([t1, t2, t3])
        assert [t.task_id for t in result.tasks] == [_uuid(), _uuid2(), _uuid3()]

    def test_does_not_call_order_tasks(self):
        t1 = _task(task_id=_uuid(), title="B", priority=TaskPriority.LOW)
        t2 = _task(task_id=_uuid2(), title="A", priority=TaskPriority.HIGH)
        result = TaskListData.from_domain([t1, t2])
        # original order [t1, t2] preserved, not sorted
        assert result.tasks[0].task_id == _uuid()
        assert result.tasks[1].task_id == _uuid2()

    def test_does_not_mutate_caller_input(self):
        t1 = _task(task_id=_uuid())
        t2 = _task(task_id=_uuid2())
        original = [t1, t2]
        original_copy = list(original)
        TaskListData.from_domain(original)
        assert original == original_copy

    def test_deterministic(self):
        tasks = [_task(), _task(task_id=_uuid2())]
        r1 = TaskListData.from_domain(tasks).model_dump()
        r2 = TaskListData.from_domain(tasks).model_dump()
        assert r1 == r2

    def test_returns_tuple_backed_immutable_data(self):
        result = TaskListData.from_domain([_task()])
        assert isinstance(result.tasks, tuple)


# ===========================================================================
# G. Response schemas
# ===========================================================================


class _ResponseData:
    @staticmethod
    def task_data() -> TaskData:
        return TaskData.from_domain(_task())

    @staticmethod
    def task_list_data() -> TaskListData:
        return TaskListData.from_domain([_task()])


class TestTaskSuccessResponse:
    def test_exact_field_names(self):
        assert set(TaskSuccessResponse.model_fields) == {"success", "message", "data"}

    def test_exact_field_order(self):
        assert list(TaskSuccessResponse.model_fields.keys()) == ["success", "message", "data"]

    def test_default_success_is_true(self):
        resp = TaskSuccessResponse(data=_ResponseData.task_data())
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            TaskSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=_ResponseData.task_data(),
            )

    def test_exact_default_message(self):
        resp = TaskSuccessResponse(data=_ResponseData.task_data())
        assert resp.message == "Task created successfully."

    def test_custom_message_accepted(self):
        resp = TaskSuccessResponse(message="Custom message.", data=_ResponseData.task_data())
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            TaskSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            TaskSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskSuccessResponse(
                data=_ResponseData.task_data(),
                extra_field="value",  # type: ignore[call-arg]
            )


class TestTaskListSuccessResponse:
    def test_exact_field_names(self):
        assert set(TaskListSuccessResponse.model_fields) == {"success", "message", "data"}

    def test_exact_field_order(self):
        assert list(TaskListSuccessResponse.model_fields.keys()) == [
            "success",
            "message",
            "data",
        ]

    def test_default_success_is_true(self):
        resp = TaskListSuccessResponse(data=_ResponseData.task_list_data())
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            TaskListSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=_ResponseData.task_list_data(),
            )

    def test_exact_default_message(self):
        resp = TaskListSuccessResponse(data=_ResponseData.task_list_data())
        assert resp.message == "Tasks retrieved successfully."

    def test_custom_message_accepted(self):
        resp = TaskListSuccessResponse(
            message="Custom message.", data=_ResponseData.task_list_data()
        )
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            TaskListSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            TaskListSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskListSuccessResponse(
                data=_ResponseData.task_list_data(),
                extra_field="value",  # type: ignore[call-arg]
            )


class TestTaskDeleteSuccessResponse:
    def test_exact_field_names(self):
        assert set(TaskDeleteSuccessResponse.model_fields) == {"success", "message"}

    def test_exact_field_order(self):
        assert list(TaskDeleteSuccessResponse.model_fields.keys()) == ["success", "message"]

    def test_default_success_is_true(self):
        resp = TaskDeleteSuccessResponse()
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            TaskDeleteSuccessResponse(success=False)  # type: ignore[arg-type]

    def test_exact_default_message(self):
        resp = TaskDeleteSuccessResponse()
        assert resp.message == "Task deleted successfully."

    def test_custom_message_accepted(self):
        resp = TaskDeleteSuccessResponse(message="Custom message.")
        assert resp.message == "Custom message."

    def test_no_data_field(self):
        assert "data" not in TaskDeleteSuccessResponse.model_fields

    def test_data_input_rejected(self):
        with pytest.raises(ValidationError):
            TaskDeleteSuccessResponse(data=_ResponseData.task_data())  # type: ignore[call-arg]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskDeleteSuccessResponse(extra_field="value")  # type: ignore[call-arg]


class TestTaskCompletionSuccessResponse:
    def test_exact_field_names(self):
        assert set(TaskCompletionSuccessResponse.model_fields) == {"success", "message", "data"}

    def test_exact_field_order(self):
        assert list(TaskCompletionSuccessResponse.model_fields.keys()) == [
            "success",
            "message",
            "data",
        ]

    def test_default_success_is_true(self):
        resp = TaskCompletionSuccessResponse(data=_ResponseData.task_data())
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            TaskCompletionSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=_ResponseData.task_data(),
            )

    def test_exact_default_message(self):
        resp = TaskCompletionSuccessResponse(data=_ResponseData.task_data())
        assert resp.message == "Task completed successfully."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            TaskCompletionSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            TaskCompletionSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskCompletionSuccessResponse(
                data=_ResponseData.task_data(),
                extra_field="value",  # type: ignore[call-arg]
            )


class TestTaskReopenSuccessResponse:
    def test_exact_field_names(self):
        assert set(TaskReopenSuccessResponse.model_fields) == {"success", "message", "data"}

    def test_exact_field_order(self):
        assert list(TaskReopenSuccessResponse.model_fields.keys()) == [
            "success",
            "message",
            "data",
        ]

    def test_default_success_is_true(self):
        resp = TaskReopenSuccessResponse(data=_ResponseData.task_data())
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            TaskReopenSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=_ResponseData.task_data(),
            )

    def test_exact_default_message(self):
        resp = TaskReopenSuccessResponse(data=_ResponseData.task_data())
        assert resp.message == "Task reopened successfully."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            TaskReopenSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            TaskReopenSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            TaskReopenSuccessResponse(
                data=_ResponseData.task_data(),
                extra_field="value",  # type: ignore[call-arg]
            )


# ===========================================================================
# H. Serialization
# ===========================================================================


class TestSerialization:
    def test_uuid_serializes_as_string(self):
        data = TaskData.from_domain(_task())
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["task_id"] == str(_uuid())

    def test_due_date_serializes_as_iso(self):
        data = TaskData.from_domain(_task(due_date=date(2025, 7, 1)))
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["due_date"] == "2025-07-01"

    def test_completed_at_serializes_as_iso_datetime(self):
        data = TaskData.from_domain(_task(status=TaskStatus.COMPLETED, completed_at=_naive_dt()))
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["completed_at"] == "2025-06-15T12:30:00"

    def test_naive_datetime_unchanged(self):
        data = TaskData.from_domain(_task(status=TaskStatus.COMPLETED, completed_at=_naive_dt()))
        assert data.completed_at.tzinfo is None

    def test_timezone_aware_datetime_preserves_offset(self):
        data = TaskData.from_domain(_task(status=TaskStatus.COMPLETED, completed_at=_tz_dt()))
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        # UTC offset must be preserved (serialized as "Z" or "+00:00"), not dropped
        assert parsed["completed_at"] not in ("2025-06-15T12:30:00", "2025-06-15T12:30:00.000")
        assert parsed["completed_at"].endswith("Z") or "+00:00" in parsed["completed_at"]

    def test_priority_serializes_lowercase(self):
        for priority, value in (
            (TaskPriority.LOW, "low"),
            (TaskPriority.MEDIUM, "medium"),
            (TaskPriority.HIGH, "high"),
        ):
            data = TaskData.from_domain(_task(priority=priority))
            raw = data.model_dump_json()
            parsed = json.loads(raw)
            assert parsed["priority"] == value

    def test_status_serializes_lowercase(self):
        for status, value in (
            (TaskStatus.PENDING, "pending"),
            (TaskStatus.COMPLETED, "completed"),
        ):
            completed = status is TaskStatus.COMPLETED
            data = TaskData.from_domain(
                _task(status=status, completed_at=(_naive_dt() if completed else None))
            )
            raw = data.model_dump_json()
            parsed = json.loads(raw)
            assert parsed["status"] == value

    def test_none_values_serialize_consistently(self):
        data = TaskData.from_domain(_task(description=None, due_date=None))
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["description"] is None
        assert parsed["due_date"] is None

    def test_no_user_id(self):
        data = TaskData.from_domain(_task())
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert "user_id" not in parsed

    def test_no_orm_id(self):
        data = TaskData.from_domain(_task())
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert "id" not in parsed

    def test_no_extra_timestamps(self):
        data = TaskData.from_domain(_task(status=TaskStatus.COMPLETED, completed_at=_naive_dt()))
        raw = data.model_dump_json()
        parsed = json.loads(raw)
        assert "created_at" not in parsed
        assert "updated_at" not in parsed

    def test_success_response_serialization(self):
        resp = TaskSuccessResponse(data=TaskData.from_domain(_task()))
        raw = resp.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["success"] is True
        assert parsed["message"] == "Task created successfully."
        assert parsed["data"]["task_id"] == str(_uuid())


# ===========================================================================
# I. Architecture and purity
# ===========================================================================


class TestSchemaPurity:
    def test_no_fastapi_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "fastapi" not in source.lower()

    def test_no_starlette_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "starlette" not in source.lower()

    def test_no_sqlalchemy_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "sqlalchemy" not in source.lower()

    def test_no_alembic_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "alembic" not in source.lower()

    def test_no_database_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.db" not in source
        assert "import app.db" not in source

    def test_no_repository_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "repositories" not in source

    def test_no_service_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.services" not in source

    def test_no_api_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_environment_access(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "os.environ" not in source
        assert "getenv" not in source

    def test_no_network_access(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "import request" not in source.lower()
        assert "urllib" not in source.lower()
        assert "httpx" not in source.lower()

    def test_no_system_clock(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_no_random(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "random" not in source.lower()

    def test_no_ai_llm(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in source.lower()

    def test_only_allowed_imports(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        allowed = (
            "from __future__",
            "from collections.abc",
            "from datetime",
            "from typing",
            "from uuid",
            "from pydantic",
            "from app.core.tasks",
        )
        lines = [
            ln
            for ln in source.splitlines()
            if ln.strip().startswith("import ") or ln.strip().startswith("from ")
        ]
        for ln in lines:
            assert any(ln.strip().startswith(a) for a in allowed), f"unexpected import: {ln!r}"


# ===========================================================================
# J. Dependency direction
# ===========================================================================


class TestDependencyDirection:
    def test_schema_may_import_domain(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.core.tasks" in source

    def test_domain_must_not_import_pydantic(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "pydantic" not in source.lower()

    def test_domain_must_not_import_schema_module(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "from app.schemas" not in source

    def test_no_circular_dependency(self):
        import app.core.tasks
        import app.schemas.tasks

        assert app.core.tasks is not None
        assert app.schemas.tasks is not None


# ===========================================================================
# K. Phase boundaries
# ===========================================================================


class TestPhaseBoundaries:
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

    def test_existing_route_inventory_unchanged(self):
        from app.main import create_app

        app = create_app()
        route_paths = sorted(r.path for r in app.routes if hasattr(r, "path"))
        expected_api_paths = {
            "/api/v1/ai-coach/chat",
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/auth/register",
            "/api/v1/auth/supabase-sync",
            "/api/v1/body-weights",
            "/api/v1/body-weights/{entry_id}",
            "/api/v1/body-weights/trend",
            "/api/v1/body-weights/goal-progress",
            "/api/v1/food-recognition/analyze",
            "/api/v1/food-search/search",
            "/api/v1/goals",
            "/api/v1/goals/{goal_id}",
            "/api/v1/health",
            "/api/v1/nutrition-logs",
            "/api/v1/nutrition-logs/progress",
            "/api/v1/nutrition-logs/summary",
            "/api/v1/nutrition-logs/{entry_id}",
            "/api/v1/nutrition-profile",
            "/api/v1/nutrition-profile/calculations",
            "/api/v1/nutrition-profile/summary",
            "/api/v1/search",
            "/api/v1/settings/account",
            "/api/v1/settings/export",
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        }
        actual_api_paths = {p for p in route_paths if p.startswith("/api/")}
        assert actual_api_paths == expected_api_paths

    def test_no_reminder_fields(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        for token in ("reminder", "recurrence", "notification", "recommendation"):
            assert token not in source.lower()
