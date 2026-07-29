from __future__ import annotations


class GoalError(Exception):
    """Base goal-domain exception."""


class GoalNotFoundError(GoalError):
    """Raised when a goal is expected but does not exist."""

    def __init__(
        self,
        message: str = "Goal not found.",
    ) -> None:
        super().__init__(message)


class GoalAlreadyExistsError(GoalError):
    """Raised when attempting to create a duplicate goal."""

    def __init__(
        self,
        message: str = "A goal with the same title already exists for this user.",
    ) -> None:
        super().__init__(message)
