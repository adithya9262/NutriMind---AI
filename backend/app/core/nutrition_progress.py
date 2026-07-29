from __future__ import annotations

import enum
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.core.nutrition_calculations import NutritionTargetResult
from app.core.nutrition_logs import DailyNutritionTotals
from app.core.nutrition_progress_exceptions import InvalidNutritionProgressInputError


class NutritionProgressStatus(enum.StrEnum):
    BELOW_TARGET = "below_target"
    TARGET_MET = "target_met"
    ABOVE_TARGET = "above_target"


@dataclass(frozen=True, slots=True)
class NutrientProgress:
    consumed: Decimal
    target: Decimal
    remaining: Decimal
    percentage: Decimal
    status: NutritionProgressStatus


@dataclass(frozen=True, slots=True)
class DailyNutritionProgress:
    calories: NutrientProgress
    protein: NutrientProgress
    carbohydrate: NutrientProgress
    fat: NutrientProgress


def _validate_consumed(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise InvalidNutritionProgressInputError(f"{field_name} must be a Decimal, not a boolean")
    if not isinstance(value, Decimal):
        raise InvalidNutritionProgressInputError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise InvalidNutritionProgressInputError(f"{field_name} must be a finite number")
    if value < Decimal("0"):
        raise InvalidNutritionProgressInputError(f"{field_name} must not be negative")
    return value


def _validate_target(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise InvalidNutritionProgressInputError(f"{field_name} must be a Decimal, not a boolean")
    if not isinstance(value, Decimal):
        raise InvalidNutritionProgressInputError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise InvalidNutritionProgressInputError(f"{field_name} must be a finite number")
    if value <= Decimal("0"):
        raise InvalidNutritionProgressInputError(f"{field_name} must be positive")
    return value


def _calculate_nutrient_progress(
    consumed: Decimal,
    target: Decimal,
) -> NutrientProgress:
    remaining = target - consumed
    percentage = (consumed / target * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    if consumed < target:
        status = NutritionProgressStatus.BELOW_TARGET
    elif consumed == target:
        status = NutritionProgressStatus.TARGET_MET
    else:
        status = NutritionProgressStatus.ABOVE_TARGET

    return NutrientProgress(
        consumed=consumed,
        target=target,
        remaining=remaining,
        percentage=percentage,
        status=status,
    )


def calculate_daily_nutrition_progress(
    *,
    totals: DailyNutritionTotals,
    targets: NutritionTargetResult,
) -> DailyNutritionProgress:
    calories = _calculate_nutrient_progress(
        consumed=_validate_consumed(totals.calories_kcal, "calories_kcal"),
        target=_validate_target(targets.calorie_target_kcal_per_day, "calorie_target_kcal_per_day"),
    )
    protein = _calculate_nutrient_progress(
        consumed=_validate_consumed(totals.protein_g, "protein_g"),
        target=_validate_target(targets.protein_g_per_day, "protein_g_per_day"),
    )
    carbohydrate = _calculate_nutrient_progress(
        consumed=_validate_consumed(totals.carbohydrate_g, "carbohydrate_g"),
        target=_validate_target(targets.carbohydrate_g_per_day, "carbohydrate_g_per_day"),
    )
    fat = _calculate_nutrient_progress(
        consumed=_validate_consumed(totals.fat_g, "fat_g"),
        target=_validate_target(targets.fat_g_per_day, "fat_g_per_day"),
    )
    return DailyNutritionProgress(
        calories=calories,
        protein=protein,
        carbohydrate=carbohydrate,
        fat=fat,
    )
