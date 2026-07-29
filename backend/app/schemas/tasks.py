from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.tasks import (
    MAX_TASK_DESCRIPTION_LENGTH,
    MAX_TASK_TITLE_LENGTH,
    MIN_TASK_TITLE_LENGTH,
    Task,
    TaskCategory,
    TaskPriority,
    TaskRecurrence,
    TaskStatus,
)

# Control characters permitted inside task text descriptions. Newlines and
# carriage returns are preserved as line breaks; titles reject all control
# characters.
_ALLOWED_DESCRIPTION_CONTROL: frozenset[str] = frozenset({"\n", "\r"})


# ---------------------------------------------------------------------------
# Shared text-validation helpers (schema-boundary, public-constant based)
# ---------------------------------------------------------------------------


def _reject_title_control_characters(value: str) -> None:
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127:
            raise ValueError("title must not contain control characters")


def _reject_description_control_characters(value: str) -> None:
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127:
            if ch in _ALLOWED_DESCRIPTION_CONTROL:
                continue
            raise ValueError("description must not contain control characters")


def _validate_title(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValueError("title must be a string")
    if "\0" in value:
        raise ValueError("title must not contain null bytes")
    _reject_title_control_characters(value)
    normalized = value.strip()
    if len(normalized) < MIN_TASK_TITLE_LENGTH:
        raise ValueError("title must not be empty or whitespace-only")
    if len(normalized) > MAX_TASK_TITLE_LENGTH:
        raise ValueError(f"title must not exceed {MAX_TASK_TITLE_LENGTH} characters")
    return normalized


def _validate_description(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValueError("description must be a string or None")
    if "\0" in value:
        raise ValueError("description must not contain null bytes")
    _reject_description_control_characters(value)
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_TASK_DESCRIPTION_LENGTH:
        raise ValueError(f"description must not exceed {MAX_TASK_DESCRIPTION_LENGTH} characters")
    return normalized


def _validate_due_date(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        raise ValueError("due_date must be a date, not a datetime")
    if isinstance(value, str):
        try:
            # Accept ISO format date strings like "2024-01-15"
            parts = value.split("-")
            if len(parts) != 3:
                raise ValueError
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            raise ValueError("due_date must be a valid date string in YYYY-MM-DD format")
    if not isinstance(value, date):
        raise ValueError("due_date must be a date instance or a date string")
    return value


# ---------------------------------------------------------------------------
# TaskCreate  (input schema)
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    category: TaskCategory = TaskCategory.CUSTOM
    recurrence: TaskRecurrence = TaskRecurrence.NONE

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str:
        return _validate_title(v)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: object) -> str | None:
        return _validate_description(v)

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v: object) -> date | None:
        return _validate_due_date(v)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    category: TaskCategory | None = None
    recurrence: TaskRecurrence | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str | None:
        if v is None:
            return None
        return _validate_title(v)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: object) -> str | None:
        if v is None:
            return None
        return _validate_description(v)

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v: object) -> date | None:
        return _validate_due_date(v)


# ---------------------------------------------------------------------------
# TaskData  (public response schema)
# ---------------------------------------------------------------------------


class TaskData(BaseModel):
    task_id: UUID
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    due_date: date | None
    completed_at: datetime | None
    category: TaskCategory
    recurrence: TaskRecurrence

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        from_attributes=True,
    )

    @model_validator(mode="after")
    def _validate_state_invariant(self) -> TaskData:
        if self.status is TaskStatus.PENDING and self.completed_at is not None:
            raise ValueError("A pending task must not have a completion timestamp.")
        if self.status is TaskStatus.COMPLETED and self.completed_at is None:
            raise ValueError("A completed task must have a completion timestamp.")
        return self

    @classmethod
    def from_domain(cls, task: Task) -> TaskData:
        if not isinstance(task, Task):
            raise TypeError("task must be a Task instance")
        return cls(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            due_date=task.due_date,
            completed_at=task.completed_at,
            category=task.category,
            recurrence=task.recurrence,
        )


# ---------------------------------------------------------------------------
# TaskListData  (collection response schema)
# ---------------------------------------------------------------------------


class TaskListData(BaseModel):
    tasks: tuple[TaskData, ...]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @classmethod
    def from_domain(cls, tasks: Iterable[Task]) -> TaskListData:
        materialized = tuple(TaskData.from_domain(task) for task in tasks)
        return cls(tasks=materialized)


# ---------------------------------------------------------------------------
# Success response schemas
# ---------------------------------------------------------------------------


class TaskSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Task created successfully."
    data: TaskData

    model_config = ConfigDict(extra="forbid")


class TaskListSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Tasks retrieved successfully."
    data: TaskListData

    model_config = ConfigDict(extra="forbid")


class TaskDeleteSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Task deleted successfully."

    model_config = ConfigDict(extra="forbid")


class TaskCompletionSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Task completed successfully."
    data: TaskData

    model_config = ConfigDict(extra="forbid")


class TaskReopenSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Task reopened successfully."
    data: TaskData

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "TaskCompletionSuccessResponse",
    "TaskCreate",
    "TaskData",
    "TaskDeleteSuccessResponse",
    "TaskListData",
    "TaskListSuccessResponse",
    "TaskReopenSuccessResponse",
    "TaskSuccessResponse",
    "TaskUpdate",
]
