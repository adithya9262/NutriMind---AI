from __future__ import annotations


class BodyWeightTrendError(Exception):
    """Base exception for body-weight trend domain errors."""


class InsufficientBodyWeightHistoryError(BodyWeightTrendError):
    """Raised when fewer than two body-weight entries are supplied for trend calculation."""

    def __init__(
        self,
        message: str = ("At least two body-weight entries are required to calculate a trend."),
    ) -> None:
        super().__init__(message)
