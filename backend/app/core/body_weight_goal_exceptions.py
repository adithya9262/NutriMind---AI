from __future__ import annotations


class BodyWeightGoalError(Exception):
    """Base exception for body-weight goal domain errors."""

    def __init__(
        self,
        message: str = (
            "Body-weight goal weights must be finite Decimal values within the supported range."
        ),
    ) -> None:
        super().__init__(message)


class InvalidBodyWeightGoalProgressError(BodyWeightGoalError):
    """Raised when body-weight goal progress cannot be calculated."""

    def __init__(
        self,
        message: str = (
            "Body-weight goal progress requires a starting weight that differs "
            "from the target weight."
        ),
    ) -> None:
        super().__init__(message)


class BodyWeightGoalCurrentWeightNotFoundError(BodyWeightGoalError):
    """Raised when no body-weight entry exists to use as the current weight."""

    def __init__(
        self,
        message: str = ("At least one body-weight entry is required to calculate goal progress."),
    ) -> None:
        super().__init__(message)
