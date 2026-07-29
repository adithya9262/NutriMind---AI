from __future__ import annotations


class NutritionProfileError(Exception):
    """Base nutrition-profile-domain exception."""


class NutritionProfileNotFoundError(NutritionProfileError):
    """Raised when a nutrition profile is expected but does not exist."""

    def __init__(
        self,
        message: str = "Nutrition profile not found.",
    ) -> None:
        super().__init__(message)


class NutritionProfileAlreadyExistsError(NutritionProfileError):
    """Raised when attempting to create a second nutrition profile for the same user."""

    def __init__(
        self,
        message: str = "A nutrition profile already exists for this user.",
    ) -> None:
        super().__init__(message)


class NutritionProfilePersistenceError(NutritionProfileError):
    """Raised when an unexpected persistence error occurs."""

    def __init__(
        self,
        message: str = "Unable to save the nutrition profile.",
    ) -> None:
        super().__init__(message)
