from __future__ import annotations


class BodyWeightError(Exception):
    """Base exception for body-weight domain errors."""


class InvalidBodyWeightError(BodyWeightError):
    """Raised when a body-weight entry contains invalid domain data."""

    def __init__(
        self,
        message: str = "The body-weight entry contains invalid data.",
    ) -> None:
        super().__init__(message)


class DuplicateBodyWeightDateError(BodyWeightError):
    """Raised when a body-weight entry already exists for the selected date."""

    def __init__(
        self,
        message: str = "A body-weight entry already exists for the selected date.",
    ) -> None:
        super().__init__(message)


class DuplicateBodyWeightEntryIdError(BodyWeightError):
    """Raised when a body-weight entry already exists with the same entry ID."""

    def __init__(
        self,
        message: str = "A body-weight entry already exists with this entry ID.",
    ) -> None:
        super().__init__(message)


class BodyWeightNotFoundError(BodyWeightError):
    """Raised when a body-weight entry is not found."""

    def __init__(
        self,
        message: str = "Body-weight entry was not found.",
    ) -> None:
        super().__init__(message)
