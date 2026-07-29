from __future__ import annotations

import enum
from dataclasses import dataclass
from decimal import Decimal

from app.core.nutrition_calculations import MINIMUM_CALORIE_TARGET, BMICategory
from app.models.enums import NutritionGoal

# ---------------------------------------------------------------------------
# Tone
# ---------------------------------------------------------------------------


class NutritionSummaryTone(enum.StrEnum):
    INFORMATIONAL = "informational"
    CAUTION = "caution"


# ---------------------------------------------------------------------------
# Summary domain types (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NutritionSummaryItem:
    """A single deterministic, machine-readable summary entry."""

    code: str
    title: str
    message: str
    tone: NutritionSummaryTone


@dataclass(frozen=True, slots=True)
class NutritionSummaryResult:
    """An immutable nutrition summary built from verified calculation results."""

    overview: str
    items: tuple[NutritionSummaryItem, ...]


# ---------------------------------------------------------------------------
# Validation helpers (Decimal-safe, no float conversion)
# ---------------------------------------------------------------------------


def _require_positive_decimal(value: object, name: str) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be a finite number")
    if value <= Decimal("0"):
        raise ValueError(f"{name} must be positive")


def _require_bmi_category(value: object) -> BMICategory:
    if not isinstance(value, BMICategory):
        raise ValueError("metrics.bmi_category must be a valid BMICategory")
    return value


def _require_goal(value: object) -> NutritionGoal:
    if not isinstance(value, NutritionGoal):
        raise ValueError("goal must be a valid NutritionGoal")
    return value


# ---------------------------------------------------------------------------
# Message builders (deterministic, rule-based)
# ---------------------------------------------------------------------------


def _bmi_message(*, bmi: Decimal, category: BMICategory) -> str:
    bmi_text = f"Your BMI is {bmi} ({category.value.replace('_', ' ')})."
    limitation = (
        " BMI is a screening measure; it does not directly measure body"
        " composition or diagnose health."
    )
    return bmi_text + limitation


def _goal_message(*, goal: NutritionGoal) -> str:
    if goal is NutritionGoal.MAINTAIN_WEIGHT:
        return (
            "This target is intended to support approximate weight maintenance."
            " Individual results are not guaranteed."
        )
    if goal is NutritionGoal.LOSE_WEIGHT:
        return (
            "This target uses a conservative calorie adjustment from the estimated"
            " TDEE. It does not predict weight loss over any specific period and no"
            " weight loss is guaranteed."
        )
    if goal is NutritionGoal.GAIN_WEIGHT:
        return (
            "This target uses a calorie increase from the estimated TDEE. It does"
            " not predict weight gain over any specific period and no weight gain is"
            " guaranteed."
        )
    if goal is NutritionGoal.GAIN_MUSCLE:
        return (
            "This target supports the selected muscle-gain goal through the existing"
            " calorie and macronutrient approach. Muscle growth and exercise outcomes"
            " are not guaranteed."
        )
    raise ValueError(f"Unsupported nutrition goal: {goal}")


# ---------------------------------------------------------------------------
# BMI tone mapping
# ---------------------------------------------------------------------------

_BMI_TONE: dict[BMICategory, NutritionSummaryTone] = {
    BMICategory.UNDERWEIGHT: NutritionSummaryTone.CAUTION,
    BMICategory.HEALTHY_WEIGHT: NutritionSummaryTone.INFORMATIONAL,
    BMICategory.OVERWEIGHT: NutritionSummaryTone.CAUTION,
    BMICategory.OBESITY: NutritionSummaryTone.CAUTION,
}


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------


def build_nutrition_summary(
    *,
    metrics: object,
    targets: object,
    goal: object,
) -> NutritionSummaryResult:
    """Build a deterministic, rule-based nutrition summary.

    The function only interprets already verified calculation results. It
    does not execute any nutrition formula and does not recalculate age, BMI,
    BMI category, BMR, TDEE, calorie target, or macronutrient targets.
    """
    from app.core.nutrition_calculations import (
        NutritionCalculationResult,
        NutritionTargetResult,
    )

    if not isinstance(metrics, NutritionCalculationResult):
        raise ValueError("metrics must be a NutritionCalculationResult")
    if not isinstance(targets, NutritionTargetResult):
        raise ValueError("targets must be a NutritionTargetResult")

    goal = _require_goal(goal)

    # --- validate supplied metrics ---------------------------------------
    age = metrics.age
    if isinstance(age, bool) or not isinstance(age, int) or age < 1:
        raise ValueError("metrics.age must be a positive integer")

    _require_positive_decimal(metrics.bmi, "metrics.bmi")
    _require_positive_decimal(metrics.bmr_kcal_per_day, "metrics.bmr_kcal_per_day")
    _require_positive_decimal(metrics.tdee_kcal_per_day, "metrics.tdee_kcal_per_day")

    bmi_category = _require_bmi_category(metrics.bmi_category)

    # --- validate supplied targets ---------------------------------------
    _require_positive_decimal(
        targets.calorie_target_kcal_per_day, "targets.calorie_target_kcal_per_day"
    )
    if targets.calorie_target_kcal_per_day < MINIMUM_CALORIE_TARGET:
        raise ValueError(
            f"targets.calorie_target_kcal_per_day must be at least {MINIMUM_CALORIE_TARGET}"
        )
    _require_positive_decimal(targets.protein_g_per_day, "targets.protein_g_per_day")
    _require_positive_decimal(targets.carbohydrate_g_per_day, "targets.carbohydrate_g_per_day")
    _require_positive_decimal(targets.fat_g_per_day, "targets.fat_g_per_day")

    # --- overview ---------------------------------------------------------
    overview = (
        "This summary is based on your verified profile calculations and selected"
        " goal. The listed values are general estimates, not medical advice or"
        " certain outcomes."
    )

    # --- items (deterministic order) -------------------------------------
    bmi_item = NutritionSummaryItem(
        code="BMI_SCREENING_CONTEXT",
        title="BMI screening context",
        message=_bmi_message(bmi=metrics.bmi, category=bmi_category),
        tone=_BMI_TONE[bmi_category],
    )

    energy_item = NutritionSummaryItem(
        code="DAILY_ENERGY_ESTIMATE",
        title="Daily energy estimate",
        message=(
            f"Your estimated basal metabolic rate (BMR) is"
            f" {metrics.bmr_kcal_per_day} kcal/day, an estimate of energy used at"
            f" rest. Your estimated total daily energy expenditure (TDEE) is"
            f" {metrics.tdee_kcal_per_day} kcal/day, based on your selected activity"
            f" level. Both are estimates, not measured values."
        ),
        tone=NutritionSummaryTone.INFORMATIONAL,
    )

    calorie_item = NutritionSummaryItem(
        code="CALORIE_TARGET_CONTEXT",
        title="Calorie-target context",
        message=(
            f"Your calorie target is {targets.calorie_target_kcal_per_day} kcal/day,"
            " a general estimate based on your verified TDEE and selected goal. It is"
            " not a guaranteed outcome and individual needs may differ."
        ),
        tone=NutritionSummaryTone.INFORMATIONAL,
    )

    macro_item = NutritionSummaryItem(
        code="MACRONUTRIENT_TARGET_CONTEXT",
        title="Macronutrient-target context",
        message=(
            f"Your estimated daily macronutrient targets are"
            f" {targets.protein_g_per_day} g protein,"
            f" {targets.carbohydrate_g_per_day} g carbohydrate, and"
            f" {targets.fat_g_per_day} g fat. These are general guidance based on"
            " your selected goal distribution, not a medical prescription."
        ),
        tone=NutritionSummaryTone.INFORMATIONAL,
    )

    goal_item = NutritionSummaryItem(
        code="GOAL_CONTEXT",
        title="Goal context",
        message=_goal_message(goal=goal),
        tone=NutritionSummaryTone.INFORMATIONAL,
    )

    limitation_item = NutritionSummaryItem(
        code="GENERAL_ESTIMATE_LIMITATION",
        title="General estimate limitation",
        message=(
            "Results are general estimates and individual needs can vary. Pregnancy,"
            " medical conditions, medications, athletic training, growth, and other"
            " individual circumstances may require guidance from a qualified"
            " healthcare or nutrition professional."
        ),
        tone=NutritionSummaryTone.CAUTION,
    )

    return NutritionSummaryResult(
        overview=overview,
        items=(
            bmi_item,
            energy_item,
            calorie_item,
            macro_item,
            goal_item,
            limitation_item,
        ),
    )
