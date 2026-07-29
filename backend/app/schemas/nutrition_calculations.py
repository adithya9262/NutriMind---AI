from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.nutrition_calculations import (
    MINIMUM_CALORIE_TARGET,
    BMICategory,
    NutritionCalculationResult,
    NutritionTargetResult,
)

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_finite_positive_decimal(value: object, field_name: str) -> Decimal:
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


def _validate_not_nan_nor_inf(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception:
            raise ValueError(f"{field_name} must be a valid decimal number")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    return value


# ---------------------------------------------------------------------------
# NutritionMetricsData
# ---------------------------------------------------------------------------


class NutritionMetricsData(BaseModel):
    age_years: int
    bmi: Decimal
    bmi_category: BMICategory
    bmr_kcal_per_day: Decimal
    tdee_kcal_per_day: Decimal

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("age_years", mode="before")
    @classmethod
    def validate_age_years(cls, v: object) -> int:
        if isinstance(v, bool):
            raise ValueError("age_years must be an integer, not a boolean")
        if not isinstance(v, int):
            raise ValueError("age_years must be an integer")
        if v < 1:
            raise ValueError("age_years must be greater than zero")
        return v

    @field_validator("bmi", mode="before")
    @classmethod
    def validate_bmi(cls, v: object) -> Decimal:
        return _validate_finite_positive_decimal(v, "BMI")

    @field_validator("bmr_kcal_per_day", mode="before")
    @classmethod
    def validate_bmr(cls, v: object) -> Decimal:
        return _validate_finite_positive_decimal(v, "BMR")

    @field_validator("tdee_kcal_per_day", mode="before")
    @classmethod
    def validate_tdee(cls, v: object) -> Decimal:
        return _validate_finite_positive_decimal(v, "TDEE")

    @classmethod
    def from_result(cls, result: NutritionCalculationResult) -> NutritionMetricsData:
        return cls(
            age_years=result.age,
            bmi=result.bmi,
            bmi_category=result.bmi_category,
            bmr_kcal_per_day=result.bmr_kcal_per_day,
            tdee_kcal_per_day=result.tdee_kcal_per_day,
        )


# ---------------------------------------------------------------------------
# NutritionTargetsData
# ---------------------------------------------------------------------------


class NutritionTargetsData(BaseModel):
    calorie_target_kcal_per_day: Decimal
    protein_g_per_day: Decimal
    carbohydrate_g_per_day: Decimal
    fat_g_per_day: Decimal

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("calorie_target_kcal_per_day", mode="before")
    @classmethod
    def validate_calorie_target(cls, v: object) -> Decimal:
        d = _validate_finite_positive_decimal(v, "calorie_target_kcal_per_day")
        if d < MINIMUM_CALORIE_TARGET:
            raise ValueError(
                f"calorie_target_kcal_per_day must be at least {MINIMUM_CALORIE_TARGET}"
            )
        return d

    @field_validator("protein_g_per_day", mode="before")
    @classmethod
    def validate_protein(cls, v: object) -> Decimal:
        return _validate_finite_positive_decimal(v, "protein_g_per_day")

    @field_validator("carbohydrate_g_per_day", mode="before")
    @classmethod
    def validate_carbohydrate(cls, v: object) -> Decimal:
        return _validate_finite_positive_decimal(v, "carbohydrate_g_per_day")

    @field_validator("fat_g_per_day", mode="before")
    @classmethod
    def validate_fat(cls, v: object) -> Decimal:
        return _validate_finite_positive_decimal(v, "fat_g_per_day")

    @classmethod
    def from_result(cls, result: NutritionTargetResult) -> NutritionTargetsData:
        return cls(
            calorie_target_kcal_per_day=result.calorie_target_kcal_per_day,
            protein_g_per_day=result.protein_g_per_day,
            carbohydrate_g_per_day=result.carbohydrate_g_per_day,
            fat_g_per_day=result.fat_g_per_day,
        )


# ---------------------------------------------------------------------------
# CalculatedNutritionData
# ---------------------------------------------------------------------------


class CalculatedNutritionData(BaseModel):
    metrics: NutritionMetricsData
    targets: NutritionTargetsData

    model_config = ConfigDict(extra="forbid", frozen=True)

    @classmethod
    def from_results(
        cls,
        metrics: NutritionCalculationResult,
        targets: NutritionTargetResult,
    ) -> CalculatedNutritionData:
        return cls(
            metrics=NutritionMetricsData.from_result(metrics),
            targets=NutritionTargetsData.from_result(targets),
        )


# ---------------------------------------------------------------------------
# CalculatedNutritionSuccessResponse
# ---------------------------------------------------------------------------


class CalculatedNutritionSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Nutrition calculations completed successfully."
    data: CalculatedNutritionData | None = None

    model_config = ConfigDict(extra="forbid")
