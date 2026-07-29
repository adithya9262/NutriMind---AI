from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType

from app.core.nutrition_calculation_exceptions import (
    CalorieTargetBelowMinimumError,
    UnsupportedBMRCalculationError,
)
from app.models.enums import ActivityLevel, BiologicalSex, NutritionGoal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIN_HEIGHT_CM = Decimal("50")
_MAX_HEIGHT_CM = Decimal("300")
_MIN_WEIGHT_KG = Decimal("10")
_MAX_WEIGHT_KG = Decimal("700")

MINIMUM_CALORIE_TARGET: Decimal = Decimal("1200")

PROTEIN_KCAL_PER_GRAM: Decimal = Decimal("4")
CARBOHYDRATE_KCAL_PER_GRAM: Decimal = Decimal("4")
FAT_KCAL_PER_GRAM: Decimal = Decimal("9")

# ---------------------------------------------------------------------------
# BMI category
# ---------------------------------------------------------------------------


class BMICategory(enum.StrEnum):
    UNDERWEIGHT = "underweight"
    HEALTHY_WEIGHT = "healthy_weight"
    OVERWEIGHT = "overweight"
    OBESITY = "obesity"


# ---------------------------------------------------------------------------
# Activity multipliers (immutable)
# ---------------------------------------------------------------------------

ACTIVITY_MULTIPLIERS: MappingProxyType[ActivityLevel, Decimal] = MappingProxyType(
    {
        ActivityLevel.SEDENTARY: Decimal("1.2"),
        ActivityLevel.LIGHTLY_ACTIVE: Decimal("1.375"),
        ActivityLevel.MODERATELY_ACTIVE: Decimal("1.55"),
        ActivityLevel.VERY_ACTIVE: Decimal("1.725"),
        ActivityLevel.EXTRA_ACTIVE: Decimal("1.9"),
    }
)

CALORIE_ADJUSTMENTS: MappingProxyType[NutritionGoal, Decimal] = MappingProxyType(
    {
        NutritionGoal.LOSE_WEIGHT: Decimal("-500"),
        NutritionGoal.MAINTAIN_WEIGHT: Decimal("0"),
        NutritionGoal.GAIN_WEIGHT: Decimal("300"),
        NutritionGoal.GAIN_MUSCLE: Decimal("250"),
    }
)

# ---------------------------------------------------------------------------
# 1. Age
# ---------------------------------------------------------------------------


def calculate_age(
    *,
    date_of_birth: date,
    reference_date: date,
) -> int:
    """Calculate completed chronological age.

    Parameters
    ----------
    date_of_birth
        The person's date of birth.
    reference_date
        The date at which to calculate the age.  Must be strictly after
        *date_of_birth*.

    Returns
    -------
    int
        Completed whole years.

    Raises
    ------
    ValueError
        If *date_of_birth* is not earlier than *reference_date*.
    """
    if date_of_birth >= reference_date:
        raise ValueError("date_of_birth must be earlier than reference_date")

    age = reference_date.year - date_of_birth.year

    birthday_this_year = _birthday_in_year(date_of_birth, reference_date.year)

    if reference_date < birthday_this_year:
        age -= 1

    return age


def _birthday_in_year(dob: date, year: int) -> date:
    """Return the birthday of *dob* that falls within *year*.

    February 29 is mapped to February 28 in non-leap years so that a
    person born on a leap day is considered to have had their birthday
    on February 28 in common years.
    """
    try:
        return dob.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


# ---------------------------------------------------------------------------
# 2. BMI
# ---------------------------------------------------------------------------


def calculate_bmi(
    *,
    height_cm: Decimal,
    weight_kg: Decimal,
) -> Decimal:
    """Calculate body mass index (BMI).

    Formula
    -------
    BMI = weight_kg / (height_m ** 2)

    where height_m = height_cm / 100.

    Uses standard metric BMI (CDC / WHO-aligned adult screening).

    Parameters
    ----------
    height_cm
        Height in centimetres (50-300).
    weight_kg
        Weight in kilograms (10-700).

    Returns
    -------
    Decimal
        BMI rounded to two decimal places (ROUND_HALF_UP).

    Raises
    ------
    ValueError
        If inputs are missing, non-finite, zero, negative, or outside the
        supported range.
    """
    _validate_finite_positive(height_cm, "height_cm")
    _validate_finite_positive(weight_kg, "weight_kg")

    if height_cm < _MIN_HEIGHT_CM:
        raise ValueError(f"height_cm must be at least {_MIN_HEIGHT_CM}")
    if height_cm > _MAX_HEIGHT_CM:
        raise ValueError(f"height_cm must be at most {_MAX_HEIGHT_CM}")
    if weight_kg < _MIN_WEIGHT_KG:
        raise ValueError(f"weight_kg must be at least {_MIN_WEIGHT_KG}")
    if weight_kg > _MAX_WEIGHT_KG:
        raise ValueError(f"weight_kg must be at most {_MAX_WEIGHT_KG}")

    height_m = height_cm / Decimal("100")
    bmi = weight_kg / (height_m * height_m)
    return bmi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# 3. BMI category
# ---------------------------------------------------------------------------


def classify_bmi(
    *,
    bmi: Decimal,
) -> BMICategory:
    """Classify an adult BMI value into a screening category.

    Thresholds (CDC / WHO-aligned adult screening)
    -----------------------------------------------
    - ``underweight``:       BMI < 18.5
    - ``healthy_weight``:    18.5 <= BMI < 25.0
    - ``overweight``:        25.0 <= BMI < 30.0
    - ``obesity``:           BMI >= 30.0

    Classification is performed on the exact supplied *bmi* value.
    The result should be displayed alongside the rounded BMI, but the
    category decision itself uses the unrounded input to avoid
    threshold-crossing errors.

    Parameters
    ----------
    bmi
        A BMI value (must be finite and positive).

    Returns
    -------
    BMICategory

    Raises
    ------
    ValueError
        If *bmi* is non-finite, zero, or negative.
    """
    _validate_finite_positive(bmi, "bmi")

    if bmi < Decimal("18.5"):
        return BMICategory.UNDERWEIGHT
    if bmi < Decimal("25.0"):
        return BMICategory.HEALTHY_WEIGHT
    if bmi < Decimal("30.0"):
        return BMICategory.OVERWEIGHT
    return BMICategory.OBESITY


# ---------------------------------------------------------------------------
# 4. BMR  (Mifflin – St Jeor)
# ---------------------------------------------------------------------------


def calculate_bmr(
    *,
    biological_sex: BiologicalSex,
    age: int,
    height_cm: Decimal,
    weight_kg: Decimal,
) -> Decimal:
    """Calculate basal metabolic rate (BMR) using the Mifflin-St Jeor equation.

    Formula
    -------
    **Male**
        BMR = 10 x weight_kg + 6.25 x height_cm - 5 x age + 5
    **Female**
        BMR = 10 x weight_kg + 6.25 x height_cm - 5 x age - 161

    The equation defines sex-specific constants for male and female only.
    It does not define an evidence-based constant for ``other`` or
    ``prefer_not_to_say``; requesting BMR for those values raises
    ``UnsupportedBMRCalculationError``.

    Parameters
    ----------
    biological_sex
        One of ``BiologicalSex.MALE`` or ``BiologicalSex.FEMALE``.
    age
        Completed years (positive integer).
    height_cm
        Height in centimetres (50-300).
    weight_kg
        Weight in kilograms (10-700).

    Returns
    -------
    Decimal
        BMR in kcal/day, rounded to the nearest whole number
        (ROUND_HALF_UP).

    Raises
    ------
    UnsupportedBMRCalculationError
        If *biological_sex* is ``other`` or ``prefer_not_to_say``.
    ValueError
        If *age* is not a positive integer, or if height/weight are
        missing, non-finite, or outside the supported range.
    """
    if not isinstance(age, int) or isinstance(age, bool):
        raise ValueError("age must be an integer")
    if age < 1:
        raise ValueError("age must be positive")

    _validate_finite_positive(height_cm, "height_cm")
    _validate_finite_positive(weight_kg, "weight_kg")

    if height_cm < _MIN_HEIGHT_CM:
        raise ValueError(f"height_cm must be at least {_MIN_HEIGHT_CM}")
    if height_cm > _MAX_HEIGHT_CM:
        raise ValueError(f"height_cm must be at most {_MAX_HEIGHT_CM}")
    if weight_kg < _MIN_WEIGHT_KG:
        raise ValueError(f"weight_kg must be at least {_MIN_WEIGHT_KG}")
    if weight_kg > _MAX_WEIGHT_KG:
        raise ValueError(f"weight_kg must be at most {_MAX_WEIGHT_KG}")

    if biological_sex == BiologicalSex.OTHER:
        raise UnsupportedBMRCalculationError(
            "BMR cannot be calculated with the selected biological-sex option "
            "using the Mifflin-St Jeor equation."
        )
    if biological_sex == BiologicalSex.PREFER_NOT_TO_SAY:
        raise UnsupportedBMRCalculationError(
            "BMR cannot be calculated with the selected biological-sex option "
            "using the Mifflin-St Jeor equation."
        )

    age_dec = Decimal(str(age))
    height = height_cm
    weight = weight_kg

    bmr = Decimal("10") * weight + Decimal("6.25") * height - Decimal("5") * age_dec

    if biological_sex == BiologicalSex.MALE:
        bmr += Decimal("5")
    elif biological_sex == BiologicalSex.FEMALE:
        bmr -= Decimal("161")
    else:
        raise UnsupportedBMRCalculationError(
            "BMR cannot be calculated with the selected biological-sex option "
            "using the Mifflin-St Jeor equation."
        )

    return bmr.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# 5. TDEE
# ---------------------------------------------------------------------------


def calculate_tdee(
    *,
    bmr: Decimal,
    activity_level: ActivityLevel,
) -> Decimal:
    """Calculate total daily energy expenditure (TDEE).

    Formula
    -------
    TDEE = BMR x activity_multiplier

    Activity multipliers (conventional estimation factors):
        - ``sedentary``:        1.2
        - ``lightly_active``:   1.375
        - ``moderately_active``: 1.55
        - ``very_active``:      1.725
        - ``extra_active``:    1.9

    Parameters
    ----------
    bmr
        Basal metabolic rate in kcal/day (must be finite and positive).
    activity_level
        An ``ActivityLevel`` enum member.

    Returns
    -------
    Decimal
        TDEE in kcal/day, rounded to the nearest whole number
        (ROUND_HALF_UP).

    Raises
    ------
    ValueError
        If *bmr* is non-finite, zero, or negative, or if
        *activity_level* is not a supported ``ActivityLevel``.
    """
    _validate_finite_positive(bmr, "bmr")

    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level)
    if multiplier is None:
        raise ValueError(f"Unsupported activity level: {activity_level}")

    tdee = bmr * multiplier
    return tdee.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# 7. Calorie target
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MacroDistribution:
    """Immutable macronutrient percentage distribution for a nutrition goal."""

    protein: Decimal
    fat: Decimal
    carbohydrate: Decimal


MACRO_DISTRIBUTIONS: MappingProxyType[NutritionGoal, MacroDistribution] = MappingProxyType(
    {
        NutritionGoal.MAINTAIN_WEIGHT: MacroDistribution(
            protein=Decimal("0.25"),
            fat=Decimal("0.30"),
            carbohydrate=Decimal("0.45"),
        ),
        NutritionGoal.LOSE_WEIGHT: MacroDistribution(
            protein=Decimal("0.30"),
            fat=Decimal("0.30"),
            carbohydrate=Decimal("0.40"),
        ),
        NutritionGoal.GAIN_WEIGHT: MacroDistribution(
            protein=Decimal("0.25"),
            fat=Decimal("0.25"),
            carbohydrate=Decimal("0.50"),
        ),
        NutritionGoal.GAIN_MUSCLE: MacroDistribution(
            protein=Decimal("0.30"),
            fat=Decimal("0.25"),
            carbohydrate=Decimal("0.45"),
        ),
    }
)


@dataclass(frozen=True, slots=True)
class MacronutrientTargets:
    """Immutable macronutrient targets in grams per day."""

    protein_g_per_day: Decimal
    carbohydrate_g_per_day: Decimal
    fat_g_per_day: Decimal


@dataclass(frozen=True, slots=True)
class NutritionTargetResult:
    """Immutable combined calorie and macronutrient target result."""

    calorie_target_kcal_per_day: Decimal
    protein_g_per_day: Decimal
    carbohydrate_g_per_day: Decimal
    fat_g_per_day: Decimal


def calculate_calorie_target(
    *,
    tdee_kcal_per_day: Decimal,
    goal: NutritionGoal,
) -> Decimal:
    """Calculate a daily calorie target from TDEE and nutrition goal.

    The target is derived by applying a fixed adjustment to the estimated
    TDEE based on the selected goal.  Adjustments are general product
    defaults and do not guarantee a particular weight-change rate.

    Parameters
    ----------
    tdee_kcal_per_day
        Total daily energy expenditure in kcal/day (must be finite and
        positive).
    goal
        A ``NutritionGoal`` enum member.

    Returns
    -------
    Decimal
        Calorie target in whole kcal/day (ROUND_HALF_UP).

    Raises
    ------
    ValueError
        If *tdee_kcal_per_day* is non-finite, zero, negative, or if
        *goal* is not a supported ``NutritionGoal``.
    CalorieTargetBelowMinimumError
        If the calculated target is below the supported minimum
        (1200 kcal/day).
    """
    _validate_finite_positive(tdee_kcal_per_day, "tdee_kcal_per_day")

    adjustment = CALORIE_ADJUSTMENTS.get(goal)
    if adjustment is None:
        raise ValueError(f"Unsupported nutrition goal: {goal}")

    target = tdee_kcal_per_day + adjustment
    target = target.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    if target < MINIMUM_CALORIE_TARGET:
        raise CalorieTargetBelowMinimumError()

    return target


def calculate_macronutrient_targets(
    *,
    calorie_target_kcal_per_day: Decimal,
    goal: NutritionGoal,
) -> MacronutrientTargets:
    """Calculate daily macronutrient targets from a calorie target and goal.

    Macro percentages are applied to the calorie target, then converted
    to grams using standard energy densities (protein 4 kcal/g,
    carbohydrate 4 kcal/g, fat 9 kcal/g).  Each gram value is rounded
    independently (ROUND_HALF_UP), which may cause a small difference
    when calories are reconstructed from the rounded grams.

    Parameters
    ----------
    calorie_target_kcal_per_day
        Daily calorie target (must be finite and positive).
    goal
        A ``NutritionGoal`` enum member.

    Returns
    -------
    MacronutrientTargets

    Raises
    ------
    ValueError
        If *calorie_target_kcal_per_day* is non-finite, zero, negative,
        or if *goal* is not a supported ``NutritionGoal``.
    """
    _validate_finite_positive(calorie_target_kcal_per_day, "calorie_target_kcal_per_day")

    dist = MACRO_DISTRIBUTIONS.get(goal)
    if dist is None:
        raise ValueError(f"Unsupported nutrition goal: {goal}")

    protein_g = ((calorie_target_kcal_per_day * dist.protein) / PROTEIN_KCAL_PER_GRAM).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    carb_g = (
        (calorie_target_kcal_per_day * dist.carbohydrate) / CARBOHYDRATE_KCAL_PER_GRAM
    ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    fat_g = ((calorie_target_kcal_per_day * dist.fat) / FAT_KCAL_PER_GRAM).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    return MacronutrientTargets(
        protein_g_per_day=protein_g,
        carbohydrate_g_per_day=carb_g,
        fat_g_per_day=fat_g,
    )


def calculate_nutrition_targets(
    *,
    tdee_kcal_per_day: Decimal,
    goal: NutritionGoal,
) -> NutritionTargetResult:
    """Calculate combined daily calorie and macronutrient targets.

    Delegates to ``calculate_calorie_target`` and
    ``calculate_macronutrient_targets``.  No formula logic is duplicated.

    Parameters
    ----------
    tdee_kcal_per_day
        Total daily energy expenditure in kcal/day (must be finite and
        positive).
    goal
        A ``NutritionGoal`` enum member.

    Returns
    -------
    NutritionTargetResult

    Raises
    ------
    ValueError
        If *tdee_kcal_per_day* is non-finite, zero, negative, or if
        *goal* is not a supported ``NutritionGoal``.
    CalorieTargetBelowMinimumError
        If the calculated calorie target is below the supported minimum.
    """
    calorie_target = calculate_calorie_target(tdee_kcal_per_day=tdee_kcal_per_day, goal=goal)
    macros = calculate_macronutrient_targets(calorie_target_kcal_per_day=calorie_target, goal=goal)
    return NutritionTargetResult(
        calorie_target_kcal_per_day=calorie_target,
        protein_g_per_day=macros.protein_g_per_day,
        carbohydrate_g_per_day=macros.carbohydrate_g_per_day,
        fat_g_per_day=macros.fat_g_per_day,
    )


# ---------------------------------------------------------------------------
# 8. Combined result (Phase 4D-1 orchestration)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NutritionCalculationResult:
    """Immutable result of a complete nutrition calculation."""

    age: int
    bmi: Decimal
    bmi_category: BMICategory
    bmr_kcal_per_day: Decimal
    tdee_kcal_per_day: Decimal


def calculate_nutrition_metrics(
    *,
    date_of_birth: date,
    reference_date: date,
    biological_sex: BiologicalSex,
    height_cm: Decimal,
    weight_kg: Decimal,
    activity_level: ActivityLevel,
) -> NutritionCalculationResult:
    """Calculate all supported nutrition metrics in one call.

    This is a pure orchestrator that delegates to the individual
    calculation functions.  No formula logic is duplicated.
    """
    age = calculate_age(date_of_birth=date_of_birth, reference_date=reference_date)

    bmi_rounded = calculate_bmi(height_cm=height_cm, weight_kg=weight_kg)

    bmi_unrounded = _raw_bmi(height_cm=height_cm, weight_kg=weight_kg)
    bmi_category = classify_bmi(bmi=bmi_unrounded)

    bmr = calculate_bmr(
        biological_sex=biological_sex,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
    )

    tdee = calculate_tdee(bmr=bmr, activity_level=activity_level)

    return NutritionCalculationResult(
        age=age,
        bmi=bmi_rounded,
        bmi_category=bmi_category,
        bmr_kcal_per_day=bmr,
        tdee_kcal_per_day=tdee,
    )


def _raw_bmi(*, height_cm: Decimal, weight_kg: Decimal) -> Decimal:
    """Calculate unrounded BMI for threshold classification."""
    _validate_finite_positive(height_cm, "height_cm")
    _validate_finite_positive(weight_kg, "weight_kg")
    height_m = height_cm / Decimal("100")
    return weight_kg / (height_m * height_m)


# ---------------------------------------------------------------------------
# Shared validation helpers
# ---------------------------------------------------------------------------


def _validate_finite_positive(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be a finite number")
    if value <= Decimal("0"):
        raise ValueError(f"{name} must be positive")
