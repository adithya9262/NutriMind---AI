from __future__ import annotations


class TaskError(Exception):
    """Base exception for task-domain failures."""


class InvalidTaskError(TaskError):
    """Raised when a task contains invalid domain data."""

    default_message = "Task data is invalid."

    def __init__(self, message: str = default_message) -> None:
        super().__init__(message)


class TaskAlreadyCompletedError(TaskError):
    """Raised when attempting to complete a task that is already completed."""

    default_message = "Task is already completed."

    def __init__(self, message: str = default_message) -> None:
        super().__init__(message)


class TaskNotCompletedError(TaskError):
    """Raised when attempting to reopen a task that is not completed."""

    default_message = "Task is not completed."

    def __init__(self, message: str = default_message) -> None:
        super().__init__(message)


class TaskNotFoundError(TaskError):
    """Raised when a task is expected but does not exist or is not owned."""

    default_message = "Task was not found."

    def __init__(self, message: str = default_message) -> None:
        super().__init__(message)


class DuplicateTaskIdError(TaskError):
    """Raised when attempting to create a task with an existing task ID."""

    default_message = "A task with this task ID already exists."

    def __init__(self, message: str = default_message) -> None:
        super().__init__(message)
