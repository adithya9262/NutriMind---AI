from __future__ import annotations


class NutritionProgressError(Exception):
    """Base nutrition-progress-domain exception."""


class InvalidNutritionProgressInputError(NutritionProgressError):
    """Raised when a progress-calculation input is invalid."""

    def __init__(
        self,
        message: str = "Nutrition progress input is invalid.",
    ) -> None:
        super().__init__(message)
