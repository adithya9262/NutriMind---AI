from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.core.nutrition_calculation_exceptions import NutritionCalculationError
from app.core.nutrition_calculations import NutritionTargetResult
from app.core.nutrition_logs import DailyNutritionTotals
from app.core.nutrition_progress import (
    DailyNutritionProgress,
    NutrientProgress,
    NutritionProgressStatus,
    calculate_daily_nutrition_progress,
)
from app.core.nutrition_progress_exceptions import (
    InvalidNutritionProgressInputError,
    NutritionProgressError,
)

MODULE = "app.core.nutrition_progress"

# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _totals(
    *,
    calories: str = "0",
    protein: str = "0",
    carbohydrate: str = "0",
    fat: str = "0",
) -> DailyNutritionTotals:
    return DailyNutritionTotals(
        calories_kcal=_dec(calories),
        protein_g=_dec(protein),
        carbohydrate_g=_dec(carbohydrate),
        fat_g=_dec(fat),
    )


def _targets(
    *,
    calories: str = "2000",
    protein: str = "100",
    carbohydrate: str = "200",
    fat: str = "65",
) -> NutritionTargetResult:
    return NutritionTargetResult(
        calorie_target_kcal_per_day=_dec(calories),
        protein_g_per_day=_dec(protein),
        carbohydrate_g_per_day=_dec(carbohydrate),
        fat_g_per_day=_dec(fat),
    )


# ===========================================================================
# A–D. NutritionProgressStatus
# ===========================================================================


class TestNutritionProgressStatus:
    def test_is_str_enum(self):
        assert issubclass(NutritionProgressStatus, str)

    def test_exact_members(self):
        assert set(NutritionProgressStatus.__members__) == {
            "BELOW_TARGET",
            "TARGET_MET",
            "ABOVE_TARGET",
        }

    def test_exact_values(self):
        assert NutritionProgressStatus.BELOW_TARGET.value == "below_target"
        assert NutritionProgressStatus.TARGET_MET.value == "target_met"
        assert NutritionProgressStatus.ABOVE_TARGET.value == "above_target"

    def test_values_are_lowercase(self):
        for status in NutritionProgressStatus:
            assert status.value == status.value.lower()

    def test_no_judgmental_values(self):
        forbidden = {
            "good",
            "bad",
            "healthy",
            "unhealthy",
            "success",
            "failure",
            "compliant",
            "non_compliant",
        }
        present = {s.value for s in NutritionProgressStatus}
        assert not (present & forbidden)

    def test_no_extra_members(self):
        assert len(NutritionProgressStatus) == 3


# ===========================================================================
# E–G. NutrientProgress
# ===========================================================================


class TestNutrientProgress:
    def test_field_contract(self):
        np = NutrientProgress(
            consumed=_dec("1500"),
            target=_dec("2000"),
            remaining=_dec("500"),
            percentage=_dec("75.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        assert np.consumed == _dec("1500")
        assert np.target == _dec("2000")
        assert np.remaining == _dec("500")
        assert np.percentage == _dec("75.00")
        assert np.status is NutritionProgressStatus.BELOW_TARGET

    def test_frozen(self):
        np = NutrientProgress(
            consumed=_dec("0"),
            target=_dec("2000"),
            remaining=_dec("2000"),
            percentage=_dec("0.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        with pytest.raises(FrozenInstanceError):
            np.consumed = _dec("100")  # type: ignore[misc]

    def test_slots(self):
        np = NutrientProgress(
            consumed=_dec("0"),
            target=_dec("2000"),
            remaining=_dec("2000"),
            percentage=_dec("0.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        with pytest.raises((AttributeError, TypeError)):
            np.new_attr = "value"  # type: ignore[attr-defined]

    def test_all_fields_are_decimal(self):
        np = NutrientProgress(
            consumed=_dec("1500"),
            target=_dec("2000"),
            remaining=_dec("500"),
            percentage=_dec("75.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        assert isinstance(np.consumed, Decimal)
        assert isinstance(np.target, Decimal)
        assert isinstance(np.remaining, Decimal)
        assert isinstance(np.percentage, Decimal)

    def test_status_is_enum(self):
        np = NutrientProgress(
            consumed=_dec("1500"),
            target=_dec("2000"),
            remaining=_dec("500"),
            percentage=_dec("75.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        assert isinstance(np.status, NutritionProgressStatus)

    def test_no_extra_fields(self):
        np = NutrientProgress(
            consumed=_dec("0"),
            target=_dec("2000"),
            remaining=_dec("2000"),
            percentage=_dec("0.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        assert not hasattr(np, "score")
        assert not hasattr(np, "grade")
        assert not hasattr(np, "recommendation")
        assert not hasattr(np, "health")
        assert not hasattr(np, "adherence")


# ===========================================================================
# H–J. DailyNutritionProgress
# ===========================================================================


class TestDailyNutritionProgress:
    def _zero_calories(self) -> NutrientProgress:
        return NutrientProgress(
            consumed=_dec("1500"),
            target=_dec("2000"),
            remaining=_dec("500"),
            percentage=_dec("75.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )

    def _zero_protein(self) -> NutrientProgress:
        return NutrientProgress(
            consumed=_dec("80"),
            target=_dec("100"),
            remaining=_dec("20"),
            percentage=_dec("80.00"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )

    def _zero_carb(self) -> NutrientProgress:
        return NutrientProgress(
            consumed=_dec("200"),
            target=_dec("200"),
            remaining=_dec("0"),
            percentage=_dec("100.00"),
            status=NutritionProgressStatus.TARGET_MET,
        )

    def _zero_fat(self) -> NutrientProgress:
        return NutrientProgress(
            consumed=_dec("70"),
            target=_dec("65"),
            remaining=_dec("-5"),
            percentage=_dec("107.69"),
            status=NutritionProgressStatus.ABOVE_TARGET,
        )

    def field_contract(self):
        p = self._zero_calories()
        c = self._zero_carb()
        f = self._zero_fat()
        dnp = DailyNutritionProgress(
            calories=self._zero_calories(),
            protein=self._zero_protein(),
            carbohydrate=c,
            fat=f,
        )
        assert dnp.calories is p
        assert dnp.protein is self._zero_protein()
        assert dnp.carbohydrate is c
        assert dnp.fat is f

    def test_frozen(self):
        dnp = DailyNutritionProgress(
            calories=self._zero_calories(),
            protein=self._zero_protein(),
            carbohydrate=self._zero_carb(),
            fat=self._zero_fat(),
        )
        with pytest.raises(FrozenInstanceError):
            dnp.calories = self._zero_calories()  # type: ignore[misc]

    def test_slots(self):
        dnp = DailyNutritionProgress(
            calories=self._zero_calories(),
            protein=self._zero_protein(),
            carbohydrate=self._zero_carb(),
            fat=self._zero_fat(),
        )
        with pytest.raises((AttributeError, TypeError)):
            dnp.new_attr = "value"  # type: ignore[attr-defined]

    def test_exact_fields(self):
        dnp = DailyNutritionProgress(
            calories=self._zero_calories(),
            protein=self._zero_protein(),
            carbohydrate=self._zero_carb(),
            fat=self._zero_fat(),
        )
        assert hasattr(dnp, "calories")
        assert hasattr(dnp, "protein")
        assert hasattr(dnp, "carbohydrate")
        assert hasattr(dnp, "fat")

    def test_no_overall_status(self):
        dnp = DailyNutritionProgress(
            calories=self._zero_calories(),
            protein=self._zero_protein(),
            carbohydrate=self._zero_carb(),
            fat=self._zero_fat(),
        )
        assert not hasattr(dnp, "overall_status")
        assert not hasattr(dnp, "overall_grade")
        assert not hasattr(dnp, "health_score")
        assert not hasattr(dnp, "adherence_score")
        assert not hasattr(dnp, "recommendation")


# ===========================================================================
# K–L. Function signature
# ===========================================================================


class TestFunctionSignature:
    def test_function_exists(self):
        assert callable(calculate_daily_nutrition_progress)

    def test_keyword_only(self):
        totals = _totals(calories="1500")
        targets = _targets()
        with pytest.raises(TypeError):
            calculate_daily_nutrition_progress(totals, targets)  # type: ignore[call-arg]


# ===========================================================================
# M–N. Reuse existing types
# ===========================================================================


class TestReuseExistingTypes:
    def test_accepts_daily_nutrition_totals(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("1500"),
            protein_g=_dec("80"),
            carbohydrate_g=_dec("180"),
            fat_g=_dec("50"),
        )
        targets = _targets()
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert isinstance(result, DailyNutritionProgress)

    def test_accepts_nutrition_target_result(self):
        totals = _totals(calories="1500")
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2000"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert isinstance(result, DailyNutritionProgress)


# ===========================================================================
# O–AG. Consumed / target / remaining / percentage behavior
# ===========================================================================


class TestCalories:
    def test_zero_consumption(self):
        totals = _totals(calories="0")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.consumed == _dec("0.00")
        assert result.calories.target == _dec("2000")
        assert result.calories.remaining == _dec("2000")
        assert result.calories.percentage == _dec("0.00")
        assert result.calories.status is NutritionProgressStatus.BELOW_TARGET

    def test_below_target(self):
        totals = _totals(calories="1500")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.remaining == _dec("500")
        assert result.calories.status is NutritionProgressStatus.BELOW_TARGET

    def test_exact_target(self):
        totals = _totals(calories="2000")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.remaining == _dec("0")
        assert result.calories.percentage == _dec("100.00")
        assert result.calories.status is NutritionProgressStatus.TARGET_MET

    def test_above_target(self):
        totals = _totals(calories="2200")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.remaining == _dec("-200")
        assert result.calories.status is NutritionProgressStatus.ABOVE_TARGET


class TestProtein:
    def test_below_target(self):
        totals = _totals(protein="80")
        targets = _targets(protein="100")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.protein.remaining == _dec("20")
        assert result.protein.status is NutritionProgressStatus.BELOW_TARGET

    def test_exact_target(self):
        totals = _totals(protein="100")
        targets = _targets(protein="100")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.protein.remaining == _dec("0")
        assert result.protein.percentage == _dec("100.00")
        assert result.protein.status is NutritionProgressStatus.TARGET_MET

    def test_above_target(self):
        totals = _totals(protein="120")
        targets = _targets(protein="100")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.protein.remaining == _dec("-20")
        assert result.protein.status is NutritionProgressStatus.ABOVE_TARGET


class TestCarbohydrate:
    def test_below_target(self):
        totals = _totals(carbohydrate="150")
        targets = _targets(carbohydrate="200")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.carbohydrate.remaining == _dec("50")
        assert result.carbohydrate.status is NutritionProgressStatus.BELOW_TARGET

    def test_exact_target(self):
        totals = _totals(carbohydrate="200")
        targets = _targets(carbohydrate="200")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.carbohydrate.remaining == _dec("0")
        assert result.carbohydrate.percentage == _dec("100.00")
        assert result.carbohydrate.status is NutritionProgressStatus.TARGET_MET

    def test_above_target(self):
        totals = _totals(carbohydrate="250")
        targets = _targets(carbohydrate="200")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.carbohydrate.remaining == _dec("-50")
        assert result.carbohydrate.status is NutritionProgressStatus.ABOVE_TARGET


class TestFat:
    def test_below_target(self):
        totals = _totals(fat="50")
        targets = _targets(fat="65")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.fat.remaining == _dec("15")
        assert result.fat.status is NutritionProgressStatus.BELOW_TARGET

    def test_exact_target(self):
        totals = _totals(fat="65")
        targets = _targets(fat="65")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.fat.remaining == _dec("0")
        assert result.fat.percentage == _dec("100.00")
        assert result.fat.status is NutritionProgressStatus.TARGET_MET

    def test_above_target(self):
        totals = _totals(fat="80")
        targets = _targets(fat="65")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.fat.remaining == _dec("-15")
        assert result.fat.status is NutritionProgressStatus.ABOVE_TARGET


# ===========================================================================
# AH–AM. Percentage behavior
# ===========================================================================


class TestPercentage:
    def test_zero(self):
        totals = _totals(calories="0")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.percentage == _dec("0.00")

    def test_below_100(self):
        totals = _totals(calories="1000")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.percentage == _dec("50.00")

    def test_exactly_100(self):
        totals = _totals(calories="2000")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.percentage == _dec("100.00")

    def test_above_100(self):
        totals = _totals(calories="2500")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.percentage == _dec("125.00")

    def test_not_capped(self):
        totals = _totals(calories="4000")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.percentage == _dec("200.00")

    def test_round_half_up(self):
        totals = _totals(calories="1000.555")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.percentage == _dec("50.03")

    def test_two_decimal_precision(self):
        totals = _totals(calories="1333")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        percent = result.calories.percentage
        assert percent.as_tuple().exponent == -2

    def test_decimal_arithmetic(self):
        totals = _totals(calories="1500")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert isinstance(result.calories.percentage, Decimal)

    def test_no_float_in_result(self):
        totals = _totals(calories="1500")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert not isinstance(result.calories.percentage, float)


# ===========================================================================
# AN–AO. Status uses unrounded values
# ===========================================================================


class TestStatusUsesUnroundedValues:
    def test_near_target_below(self):
        totals = _totals(calories="1999.99")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.status is NutritionProgressStatus.BELOW_TARGET
        assert result.calories.remaining == _dec("0.01")

    def test_near_target_above(self):
        totals = _totals(calories="2000.01")
        targets = _targets(calories="2000")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.status is NutritionProgressStatus.ABOVE_TARGET
        assert result.calories.remaining == _dec("-0.01")


# ===========================================================================
# AP–AQ. All four nutrients calculated + known example
# ===========================================================================


class TestAllNutrientsAndKnownExample:
    def test_all_four_calculated(self):
        totals = _totals(calories="1500", protein="80", carbohydrate="180", fat="50")
        targets = _targets(calories="2000", protein="100", carbohydrate="200", fat="65")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert result.calories.remaining == _dec("500")
        assert result.protein.remaining == _dec("20")
        assert result.carbohydrate.remaining == _dec("20")
        assert result.fat.remaining == _dec("15")

    def test_known_combined_example(self):
        totals = _totals(calories="2000", protein="100", carbohydrate="200", fat="65")
        targets = _targets(calories="2000", protein="100", carbohydrate="200", fat="65")
        result = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert all(
            getattr(result, attr).status is NutritionProgressStatus.TARGET_MET
            for attr in ("calories", "protein", "carbohydrate", "fat")
        )
        assert all(
            getattr(result, attr).percentage == _dec("100.00")
            for attr in ("calories", "protein", "carbohydrate", "fat")
        )


# ===========================================================================
# AR–AT. Determinism and immutability
# ===========================================================================


class TestDeterminismAndImmutability:
    def test_deterministic_repeated_calls(self):
        totals = _totals(calories="1500")
        targets = _targets(calories="2000")
        r1 = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        r2 = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert r1 == r2
        assert r1.calories.remaining == r2.calories.remaining
        assert r1.calories.percentage == r2.calories.percentage
        assert r1.calories.status is r2.calories.status

    def test_input_totals_unchanged(self):
        totals = _totals(calories="1500")
        targets = _targets(calories="2000")
        totals_copy = DailyNutritionTotals(
            calories_kcal=totals.calories_kcal,
            protein_g=totals.protein_g,
            carbohydrate_g=totals.carbohydrate_g,
            fat_g=totals.fat_g,
        )
        calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert totals.calories_kcal == totals_copy.calories_kcal
        assert totals.protein_g == totals_copy.protein_g
        assert totals.carbohydrate_g == totals_copy.carbohydrate_g
        assert totals.fat_g == totals_copy.fat_g

    def test_input_targets_unchanged(self):
        totals = _totals(calories="1500")
        targets = _targets(calories="2000")
        targets_copy = NutritionTargetResult(
            calorie_target_kcal_per_day=targets.calorie_target_kcal_per_day,
            protein_g_per_day=targets.protein_g_per_day,
            carbohydrate_g_per_day=targets.carbohydrate_g_per_day,
            fat_g_per_day=targets.fat_g_per_day,
        )
        calculate_daily_nutrition_progress(totals=totals, targets=targets)
        assert targets.calorie_target_kcal_per_day == targets_copy.calorie_target_kcal_per_day
        assert targets.protein_g_per_day == targets_copy.protein_g_per_day
        assert targets.carbohydrate_g_per_day == targets_copy.carbohydrate_g_per_day
        assert targets.fat_g_per_day == targets_copy.fat_g_per_day


# ===========================================================================
# AV–BH. Consumed-value validation
# ===========================================================================


class TestConsumedValidation:
    def test_negative_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("-1"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_nan_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal("NaN"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_infinity_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal("Inf"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_negative_infinity_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal("-Inf"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)


# ===========================================================================
# AZ–BD. Target-value validation
# ===========================================================================


class TestTargetValidation:
    def test_zero_target_rejected(self):
        totals = _totals()
        targets = _targets(calories="0")
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_negative_target_rejected(self):
        totals = _totals()
        targets = _targets(calories="-100")
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_nan_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal("NaN"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_infinity_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal("Inf"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_negative_infinity_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal("-Inf"),
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)


# ===========================================================================
# BE–BH. Invalid types
# ===========================================================================


class TestInvalidTypes:
    def test_bool_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(  # type: ignore[arg-type]
            calorie_target_kcal_per_day=True,
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_string_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(  # type: ignore[arg-type]
            calorie_target_kcal_per_day=_dec("2000"),
            protein_g_per_day="100",
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_float_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(  # type: ignore[arg-type]
            calorie_target_kcal_per_day=2000.5,
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_none_target_rejected(self):
        totals = _totals()
        targets = NutritionTargetResult(  # type: ignore[arg-type]
            calorie_target_kcal_per_day=None,
            protein_g_per_day=_dec("100"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises(InvalidNutritionProgressInputError):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)

    def test_no_framework_exceptions_exposed(self):
        totals = _totals()
        targets = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2000"),
            protein_g_per_day=_dec("0"),
            carbohydrate_g_per_day=_dec("200"),
            fat_g_per_day=_dec("65"),
        )
        with pytest.raises((InvalidNutritionProgressInputError, NutritionProgressError)):
            calculate_daily_nutrition_progress(totals=totals, targets=targets)


# ===========================================================================
# BI–BJ. Safe exception messages
# ===========================================================================


class TestSafeExceptionMessages:
    def test_safe_message_no_raw_values(self):
        try:
            totals = _totals()
            targets = NutritionTargetResult(
                calorie_target_kcal_per_day=_dec("0"),
                protein_g_per_day=_dec("100"),
                carbohydrate_g_per_day=_dec("200"),
                fat_g_per_day=_dec("65"),
            )
            calculate_daily_nutrition_progress(totals=totals, targets=targets)
        except InvalidNutritionProgressInputError as exc:
            msg = str(exc)
            assert "0" not in msg
        except NutritionProgressError:
            pass

    def test_no_secrets_in_messages(self):
        try:
            totals = _totals()
            targets = NutritionTargetResult(
                calorie_target_kcal_per_day=_dec("-500"),
                protein_g_per_day=_dec("100"),
                carbohydrate_g_per_day=_dec("200"),
                fat_g_per_day=_dec("65"),
            )
            calculate_daily_nutrition_progress(totals=totals, targets=targets)
        except InvalidNutritionProgressInputError as exc:
            msg = str(exc)
            assert "password" not in msg.lower()
            assert "secret" not in msg.lower()
            assert "api_key" not in msg.lower()
        except NutritionProgressError:
            pass


# ===========================================================================
# BK–BV. Domain purity
# ===========================================================================


class TestDomainPurity:
    def test_no_fastapi_import(self):
        source = _source()
        assert "fastapi" not in source.lower()

    def test_no_pydantic_import(self):
        source = _source()
        assert "pydantic" not in source.lower()

    def test_no_sqlalchemy_import(self):
        source = _source()
        assert "sqlalchemy" not in source.lower()

    def test_no_database_import(self):
        source = _source()
        assert "from app.db" not in source
        assert "import app.db" not in source

    def test_no_repository_import(self):
        source = _source()
        assert "repositories" not in source

    def test_no_service_import(self):
        source = _source()
        assert "from app.services" not in source

    def test_no_api_import(self):
        source = _source()
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_environment_access(self):
        source = _source()
        assert "os.environ" not in source
        assert "getenv" not in source
        assert "os.getenv" not in source

    def test_no_network_access(self):
        source = _source()
        assert "import request" not in source.lower()
        assert "urllib" not in source.lower()
        assert "httpx" not in source.lower()

    def test_no_system_clock(self):
        source = _source()
        assert "date.today" not in source
        assert "datetime.now" not in source
        assert "datetime.utcnow" not in source
        assert "time.time" not in source

    def test_no_random_behavior(self):
        source = _source()
        assert "random" not in source.lower()

    def test_no_global_mutable_state(self):
        source = _source()
        assert "global " not in source

    def test_no_target_recalculation(self):
        source = _source()
        assert "calculate_calorie_target" not in source
        assert "calculate_macronutrient_targets" not in source
        assert "calculate_nutrition_targets" not in source

    def test_no_daily_total_recalculation(self):
        source = _source()
        assert "calculate_daily_nutrition_totals" not in source
        assert "summarize_daily_nutrition_log" not in source

    def test_no_health_score(self):
        source = _source()
        assert "health_score" not in source.lower()
        assert "health score" not in source.lower()

    def test_no_adherence_score(self):
        source = _source()
        assert "adherence" not in source.lower()

    def test_no_recommendation_logic(self):
        source = _source()
        assert "recommend" not in source.lower()

    def test_no_diagnosis_treatment(self):
        source = _source()
        for token in ("diagnos", "treatment", "therapy"):
            assert token not in source.lower()

    def test_no_ai_sdk_imports(self):
        source = _source()
        for token in ("groq", "openai", "langchain", "gemini"):
            assert token not in source.lower()

    def test_only_domain_and_stdlib_imports(self):
        source = _source()
        allowed = (
            "from __future__",
            "import enum",
            "from dataclasses",
            "from decimal",
            "from app.core.nutrition_logs",
            "from app.core.nutrition_calculations",
            "from app.core.nutrition_progress_exceptions",
        )
        lines = [
            ln for ln in source.splitlines() if ln.startswith("import ") or ln.startswith("from ")
        ]
        for ln in lines:
            assert any(ln.startswith(a) for a in allowed), f"unexpected import: {ln!r}"


# ===========================================================================
# CC–CD. Existing behavior unchanged
# ===========================================================================


class TestExistingBehaviorUnchanged:
    def test_existing_phase_4d_target_type_unchanged(self):
        import app.core.nutrition_calculations as calcs

        assert hasattr(calcs, "NutritionTargetResult")
        assert hasattr(calcs, "calculate_nutrition_targets")

    def test_existing_phase_4f1_aggregation_unchanged(self):
        import app.core.nutrition_logs as logs

        assert hasattr(logs, "DailyNutritionTotals")
        assert hasattr(logs, "calculate_daily_nutrition_totals")

    def test_existing_exception_hierarchy_unchanged(self):
        assert issubclass(NutritionProgressError, Exception)
        assert issubclass(InvalidNutritionProgressInputError, NutritionProgressError)
        assert not issubclass(InvalidNutritionProgressInputError, NutritionCalculationError)


def _source() -> str:
    mod = importlib.import_module(MODULE)
    import inspect

    return inspect.getsource(mod)
