from __future__ import annotations


class NutritionCalculationError(Exception):
    """Base nutrition-calculation-domain exception."""


class UnsupportedBMRCalculationError(NutritionCalculationError):
    """Raised when BMR cannot be calculated for the given biological-sex value.

    The Mifflin-St Jeor equation defines sex-specific constants for male
    and female only.  It does not define an evidence-based constant for
    ``other`` or ``prefer_not_to_say``.
    """

    def __init__(
        self,
        message: str = (
            "BMR cannot be calculated with the selected biological-sex"
            " option using the Mifflin-St Jeor equation."
        ),
    ) -> None:
        super().__init__(message)


class CalorieTargetBelowMinimumError(NutritionCalculationError):
    """Raised when the calculated calorie target is below the supported minimum.

    The general application minimum is 1200 kcal/day.  Values below this
    safety floor raise this exception rather than being silently clamped.
    """

    def __init__(
        self,
        message: str = (
            "The calculated calorie target is below the supported"
            " minimum for this general nutrition estimate."
        ),
    ) -> None:
        super().__init__(message)
