from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.nutrition_progress import (
    DailyNutritionProgress,
    NutrientProgress,
    NutritionProgressStatus,
)


def _validate_finite_non_negative(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception:
            raise ValueError(f"{field_name} must be a valid decimal number")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must not be negative")
    return value


def _validate_finite_positive(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception:
            raise ValueError(f"{field_name} must be a valid decimal number")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return value


def _validate_finite(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception:
            raise ValueError(f"{field_name} must be a valid decimal number")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    return value


class NutrientProgressData(BaseModel):
    consumed: Decimal
    target: Decimal
    remaining: Decimal
    percentage: Decimal
    status: NutritionProgressStatus

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @field_validator("consumed", mode="before")
    @classmethod
    def validate_consumed(cls, v: object) -> Decimal:
        return _validate_finite_non_negative(v, "consumed")

    @field_validator("target", mode="before")
    @classmethod
    def validate_target(cls, v: object) -> Decimal:
        return _validate_finite_positive(v, "target")

    @field_validator("remaining", mode="before")
    @classmethod
    def validate_remaining(cls, v: object) -> Decimal:
        return _validate_finite(v, "remaining")

    @field_validator("percentage", mode="before")
    @classmethod
    def validate_percentage(cls, v: object) -> Decimal:
        return _validate_finite_non_negative(v, "percentage")

    @classmethod
    def from_result(cls, result: NutrientProgress) -> NutrientProgressData:
        return cls(
            consumed=result.consumed,
            target=result.target,
            remaining=result.remaining,
            percentage=result.percentage,
            status=result.status,
        )


class DailyNutritionProgressData(BaseModel):
    calories: NutrientProgressData
    protein: NutrientProgressData
    carbohydrate: NutrientProgressData
    fat: NutrientProgressData
    requires_onboarding: bool | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @classmethod
    def from_result(cls, result: DailyNutritionProgress) -> DailyNutritionProgressData:
        return cls(
            calories=NutrientProgressData.from_result(result.calories),
            protein=NutrientProgressData.from_result(result.protein),
            carbohydrate=NutrientProgressData.from_result(result.carbohydrate),
            fat=NutrientProgressData.from_result(result.fat),
        )


class DailyNutritionProgressSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Daily nutrition target progress calculated successfully."
    data: DailyNutritionProgressData

    model_config = ConfigDict(
        extra="forbid",
    )
