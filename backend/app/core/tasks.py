from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from types import MappingProxyType
from uuid import UUID

from app.core.task_exceptions import (
    InvalidTaskError,
    TaskAlreadyCompletedError,
    TaskNotCompletedError,
)

# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

MIN_TASK_TITLE_LENGTH: int = 1
MAX_TASK_TITLE_LENGTH: int = 200
MAX_TASK_DESCRIPTION_LENGTH: int = 2000

# ---------------------------------------------------------------------------
# Task category
# ---------------------------------------------------------------------------


class TaskCategory(StrEnum):
    DAILY_HABIT = "daily_habit"
    EXERCISE = "exercise"
    WATER = "water"
    SLEEP = "sleep"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Task recurrence
# ---------------------------------------------------------------------------


class TaskRecurrence(StrEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"



# ---------------------------------------------------------------------------
# Task priority
# ---------------------------------------------------------------------------


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Immutable priority ordering: HIGH first, then MEDIUM, then LOW.
# Do not rely on alphabetical enum ordering.
_PRIORITY_ORDER: MappingProxyType[TaskPriority, int] = MappingProxyType(
    {
        TaskPriority.HIGH: 0,
        TaskPriority.MEDIUM: 1,
        TaskPriority.LOW: 2,
    }
)

# ---------------------------------------------------------------------------
# Task status
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Task record
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Task:
    task_id: UUID
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    due_date: date | None
    completed_at: datetime | None
    category: TaskCategory = TaskCategory.CUSTOM
    recurrence: TaskRecurrence = TaskRecurrence.NONE


    def __post_init__(self) -> None:
        object.__setattr__(self, "task_id", _validate_task_id(self.task_id))
        object.__setattr__(self, "title", _validate_and_normalize_title(self.title))
        object.__setattr__(
            self,
            "description",
            _validate_and_normalize_description(self.description),
        )
        object.__setattr__(self, "priority", _validate_priority(self.priority))
        object.__setattr__(self, "status", _validate_status(self.status))
        object.__setattr__(self, "due_date", _validate_due_date(self.due_date))
        object.__setattr__(self, "completed_at", _validate_completed_at(self.completed_at))
        object.__setattr__(self, "category", _validate_category(self.category))
        object.__setattr__(self, "recurrence", _validate_recurrence(self.recurrence))

        if self.status is TaskStatus.PENDING and self.completed_at is not None:
            raise InvalidTaskError("A pending task must not have a completion timestamp.")

        if self.status is TaskStatus.COMPLETED and self.completed_at is None:
            raise InvalidTaskError("A completed task must have a completion timestamp.")


# ---------------------------------------------------------------------------
# Shared validation helpers
# ---------------------------------------------------------------------------

# Control characters permitted inside task text. Newlines and carriage
# returns are preserved as line breaks in descriptions; titles reject all
# control characters.
_ALLOWED_DESCRIPTION_CONTROL: frozenset[str] = frozenset({"\n", "\r"})


def _reject_control_characters(value: str, field_name: str) -> None:
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127:
            if ch in _ALLOWED_DESCRIPTION_CONTROL:
                continue
            raise InvalidTaskError(f"{field_name} must not contain control characters")


def _validate_task_id(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    raise InvalidTaskError("task_id must be a UUID instance")


def _validate_and_normalize_title(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str):
        raise InvalidTaskError("title must be a string")
    if "\0" in value:
        raise InvalidTaskError("title must not contain null bytes")
    _reject_control_characters(value, "title")
    normalized = value.strip()
    if len(normalized) < MIN_TASK_TITLE_LENGTH:
        raise InvalidTaskError("title must not be empty or whitespace-only")
    if len(normalized) > MAX_TASK_TITLE_LENGTH:
        raise InvalidTaskError("title must not exceed 200 characters")
    return normalized


def _validate_and_normalize_description(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, str):
        raise InvalidTaskError("description must be a string or None")
    if "\0" in value:
        raise InvalidTaskError("description must not contain null bytes")
    _reject_control_characters(value, "description")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_TASK_DESCRIPTION_LENGTH:
        raise InvalidTaskError("description must not exceed 2000 characters")
    return normalized


def _validate_priority(value: object) -> TaskPriority:
    if isinstance(value, TaskPriority):
        return value
    raise InvalidTaskError("priority must be a TaskPriority member")


def _validate_status(value: object) -> TaskStatus:
    if isinstance(value, TaskStatus):
        return value
    raise InvalidTaskError("status must be a TaskStatus member")


def _validate_category(value: object) -> TaskCategory:
    if isinstance(value, TaskCategory):
        return value
    raise InvalidTaskError("category must be a TaskCategory member")


def _validate_recurrence(value: object) -> TaskRecurrence:
    if isinstance(value, TaskRecurrence):
        return value
    raise InvalidTaskError("recurrence must be a TaskRecurrence member")


def _validate_due_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime) or not isinstance(value, date):
        raise InvalidTaskError("due_date must be a date instance (not datetime)")
    return value


def _validate_completed_at(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raise InvalidTaskError("completed_at must be a datetime instance or None")


# ---------------------------------------------------------------------------
# Task creation
# ---------------------------------------------------------------------------


def create_task(
    *,
    task_id: UUID,
    title: str,
    description: str | None,
    priority: TaskPriority,
    due_date: date | None,
    category: TaskCategory = TaskCategory.CUSTOM,
    recurrence: TaskRecurrence = TaskRecurrence.NONE,
) -> Task:
    """Create a new immutable pending Task.

    All validation and normalization is delegated to ``Task.__post_init__``
    so that direct construction and factory construction share one code path.
    The resulting task is always ``PENDING`` with ``completed_at`` set to
    ``None``; the caller owns all date and time semantics.
    """
    return Task(
        task_id=task_id,
        title=title,
        description=description,
        priority=priority,
        status=TaskStatus.PENDING,
        due_date=due_date,
        completed_at=None,
        category=category,
        recurrence=recurrence,
    )


# ---------------------------------------------------------------------------
# Task editing (pure transformation)
# ---------------------------------------------------------------------------


def update_task(
    *,
    task: Task,
    title: str | None = None,
    description: str | None = None,
    priority: TaskPriority | None = None,
    due_date: date | None = None,
    category: TaskCategory | None = None,
    recurrence: TaskRecurrence | None = None,
) -> Task:
    """Return a new Task with updated fields, preserving all other fields.
    """
    if not isinstance(task, Task):
        raise InvalidTaskError("task must be a Task instance")

    new_title = title if title is not None else task.title
    # If description is provided (including empty string which becomes None), update it
    # We pass it as is to replace(), __post_init__ will normalize it.
    new_description = description if description is not None else task.description
    new_priority = priority if priority is not None else task.priority
    new_due_date = due_date if due_date is not None else task.due_date
    new_category = category if category is not None else task.category
    new_recurrence = recurrence if recurrence is not None else task.recurrence

    return replace(
        task,
        title=new_title,
        description=new_description,
        priority=new_priority,
        due_date=new_due_date,
        category=new_category,
        recurrence=new_recurrence,
    )


# ---------------------------------------------------------------------------
# Task completion (pure transformation)
# ---------------------------------------------------------------------------


def complete_task(
    *,
    task: Task,
    completed_at: datetime,
) -> Task:
    """Return a new completed Task preserving all other fields.

    The completion timestamp is the caller-provided ``completed_at``; the
    system clock is never consulted. Raises ``TaskAlreadyCompletedError`` if
    the task is already completed.
    """
    if not isinstance(task, Task):
        raise InvalidTaskError("task must be a Task instance")
    if not isinstance(completed_at, datetime):
        raise InvalidTaskError("completed_at must be a datetime instance")

    if task.status is TaskStatus.COMPLETED:
        raise TaskAlreadyCompletedError()

    return replace(task, status=TaskStatus.COMPLETED, completed_at=completed_at)


# ---------------------------------------------------------------------------
# Task reopening (pure transformation)
# ---------------------------------------------------------------------------


def reopen_task(
    *,
    task: Task,
) -> Task:
    """Return a new pending Task preserving all other fields.

    Raises ``TaskNotCompletedError`` if the task is not completed.
    """
    if not isinstance(task, Task):
        raise InvalidTaskError("task must be a Task instance")

    if task.status is not TaskStatus.COMPLETED:
        raise TaskNotCompletedError()

    return replace(task, status=TaskStatus.PENDING, completed_at=None)


# ---------------------------------------------------------------------------
# Deterministic ordering
# ---------------------------------------------------------------------------

# Sentinel date used for tasks without a due date during sorting. It sorts
# after every real date, but the explicit due-date-presence rank keeps
# undated tasks grouped after dated tasks regardless.
_NO_DUE_DATE_SENTINEL: date = date.max


def _task_sort_key(task: Task) -> tuple[object, ...]:
    status_rank = 0 if task.status is TaskStatus.PENDING else 1
    has_due_date = task.due_date is not None
    due_date_rank = 0 if has_due_date else 1
    due_date_value = task.due_date if has_due_date else _NO_DUE_DATE_SENTINEL
    priority_rank = _PRIORITY_ORDER[task.priority]
    return (
        status_rank,
        due_date_rank,
        due_date_value,
        priority_rank,
        task.title.casefold(),
        task.task_id,
    )


def order_tasks(
    *,
    tasks: Iterable[Task],
) -> tuple[Task, ...]:
    """Return tasks in deterministic order as a tuple.

    Materializes the iterable exactly once, validates every member, and
    never mutates caller-owned collections.

    Order:
      1. Pending before completed
      2. Tasks with a due date before tasks without a due date
      3. Earlier due dates before later due dates
      4. Higher priority before lower priority (HIGH, MEDIUM, LOW)
      5. Title compared case-insensitively (casefold)
      6. task_id ascending as the final tie-breaker
    """
    materialized = list(tasks)
    for item in materialized:
        if not isinstance(item, Task):
            raise InvalidTaskError("Each task must be a Task instance")
    materialized.sort(key=_task_sort_key)
    return tuple(materialized)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "MIN_TASK_TITLE_LENGTH",
    "MAX_TASK_TITLE_LENGTH",
    "MAX_TASK_DESCRIPTION_LENGTH",
    "TaskPriority",
    "TaskStatus",
    "TaskCategory",
    "TaskRecurrence",
    "Task",
    "create_task",
    "update_task",
    "complete_task",
    "reopen_task",
    "order_tasks",
]
