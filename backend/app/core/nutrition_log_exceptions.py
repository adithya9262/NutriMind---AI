from __future__ import annotations


class NutritionLogError(Exception):
    """Base exception for nutrition-log domain errors."""


class InvalidNutritionLogEntryError(NutritionLogError):
    """Raised when a nutrition-log entry contains invalid domain data."""

    def __init__(
        self,
        message: str = "Nutrition log entry data is invalid.",
    ) -> None:
        super().__init__(message)


class NutritionLogEntryNotFoundError(NutritionLogError):
    """Raised when a nutrition-log entry is expected but does not exist."""

    def __init__(
        self,
        message: str = "Nutrition log entry was not found.",
    ) -> None:
        super().__init__(message)


class NutritionLogEntryAlreadyExistsError(NutritionLogError):
    """Raised when attempting to create a duplicate nutrition-log entry."""

    def __init__(
        self,
        message: str = "A nutrition log entry with this identifier already exists.",
    ) -> None:
        super().__init__(message)


class NutritionLogPersistenceError(NutritionLogError):
    """Raised when an unexpected persistence error occurs."""

    def __init__(
        self,
        message: str = "Nutrition log data could not be saved.",
    ) -> None:
        super().__init__(message)
