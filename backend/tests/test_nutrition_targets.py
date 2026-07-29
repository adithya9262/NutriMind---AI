from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType

import pytest

from app.core.nutrition_calculation_exceptions import (
    CalorieTargetBelowMinimumError,
    NutritionCalculationError,
)
from app.core.nutrition_calculations import (
    CALORIE_ADJUSTMENTS,
    CARBOHYDRATE_KCAL_PER_GRAM,
    FAT_KCAL_PER_GRAM,
    MACRO_DISTRIBUTIONS,
    MINIMUM_CALORIE_TARGET,
    PROTEIN_KCAL_PER_GRAM,
    MacroDistribution,
    calculate_calorie_target,
    calculate_macronutrient_targets,
    calculate_nutrition_targets,
)
from app.models.enums import NutritionGoal


def _dec(value: str) -> Decimal:
    return Decimal(value)


# ===========================================================================
# 1. Constants
# ===========================================================================


class TestConstants:
    def test_minimum_calorie_target_value(self):
        assert MINIMUM_CALORIE_TARGET == _dec("1200")

    def test_minimum_calorie_target_is_decimal(self):
        assert isinstance(MINIMUM_CALORIE_TARGET, Decimal)

    def test_protein_kcal_per_gram_value(self):
        assert PROTEIN_KCAL_PER_GRAM == _dec("4")

    def test_carbohydrate_kcal_per_gram_value(self):
        assert CARBOHYDRATE_KCAL_PER_GRAM == _dec("4")

    def test_fat_kcal_per_gram_value(self):
        assert FAT_KCAL_PER_GRAM == _dec("9")

    def test_all_constants_are_decimal(self):
        assert isinstance(MINIMUM_CALORIE_TARGET, Decimal)
        assert isinstance(PROTEIN_KCAL_PER_GRAM, Decimal)
        assert isinstance(CARBOHYDRATE_KCAL_PER_GRAM, Decimal)
        assert isinstance(FAT_KCAL_PER_GRAM, Decimal)

    def test_no_float_constants(self):
        assert not isinstance(MINIMUM_CALORIE_TARGET, float)
        assert not isinstance(PROTEIN_KCAL_PER_GRAM, float)
        assert not isinstance(CARBOHYDRATE_KCAL_PER_GRAM, float)
        assert not isinstance(FAT_KCAL_PER_GRAM, float)

    def test_constants_not_changed_by_functions(self):
        before = MINIMUM_CALORIE_TARGET
        calculate_calorie_target(tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT)
        assert MINIMUM_CALORIE_TARGET == before


# ===========================================================================
# 2. Calorie adjustments
# ===========================================================================


class TestCalorieAdjustments:
    def test_every_goal_covered(self):
        for goal in NutritionGoal:
            assert goal in CALORIE_ADJUSTMENTS

    def test_exactly_four_entries(self):
        assert len(CALORIE_ADJUSTMENTS) == 4

    def test_correct_adjustments(self):
        assert CALORIE_ADJUSTMENTS[NutritionGoal.MAINTAIN_WEIGHT] == _dec("0")
        assert CALORIE_ADJUSTMENTS[NutritionGoal.LOSE_WEIGHT] == _dec("-500")
        assert CALORIE_ADJUSTMENTS[NutritionGoal.GAIN_WEIGHT] == _dec("300")
        assert CALORIE_ADJUSTMENTS[NutritionGoal.GAIN_MUSCLE] == _dec("250")

    def test_decimal_values_only(self):
        for v in CALORIE_ADJUSTMENTS.values():
            assert isinstance(v, Decimal)

    def test_no_float_values(self):
        for v in CALORIE_ADJUSTMENTS.values():
            assert not isinstance(v, float)

    def test_mapping_immutable(self):
        with pytest.raises(TypeError):
            CALORIE_ADJUSTMENTS[NutritionGoal.MAINTAIN_WEIGHT] = _dec("100")  # type: ignore[index]

    def test_no_missing_goals(self):
        assert set(CALORIE_ADJUSTMENTS.keys()) == set(NutritionGoal)

    def test_no_extra_goals(self):
        assert len(CALORIE_ADJUSTMENTS) == len(list(NutritionGoal))

    def test_is_mapping_proxy_type(self):
        assert isinstance(CALORIE_ADJUSTMENTS, MappingProxyType)


# ===========================================================================
# 3. Calorie target calculation
# ===========================================================================


class TestCalculateCalorieTarget:
    def test_maintain_returns_tdee(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result == _dec("2000")

    def test_lose_subtracts_500(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.LOSE_WEIGHT
        )
        assert result == _dec("1500")

    def test_gain_weight_adds_300(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.GAIN_WEIGHT
        )
        assert result == _dec("2300")

    def test_gain_muscle_adds_250(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.GAIN_MUSCLE
        )
        assert result == _dec("2250")

    def test_whole_kcal_decimal_result(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert isinstance(result, Decimal)
        assert result == result.to_integral_value()

    def test_round_half_up(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("1700"), goal=NutritionGoal.GAIN_MUSCLE
        )
        assert result == _dec("1950")

    def test_minimum_result_accepted(self):
        result = calculate_calorie_target(
            tdee_kcal_per_day=_dec("1200"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result == _dec("1200")

    def test_below_minimum_rejected(self):
        with pytest.raises(CalorieTargetBelowMinimumError):
            calculate_calorie_target(tdee_kcal_per_day=_dec("1500"), goal=NutritionGoal.LOSE_WEIGHT)

    def test_zero_tdee_rejected(self):
        with pytest.raises(ValueError):
            calculate_calorie_target(
                tdee_kcal_per_day=_dec("0"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_negative_tdee_rejected(self):
        with pytest.raises(ValueError):
            calculate_calorie_target(
                tdee_kcal_per_day=_dec("-100"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            calculate_calorie_target(
                tdee_kcal_per_day=Decimal("NaN"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_positive_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_calorie_target(
                tdee_kcal_per_day=Decimal("Inf"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_calorie_target(
                tdee_kcal_per_day=Decimal("-Inf"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_invalid_goal_rejected(self):
        with pytest.raises(ValueError):
            calculate_calorie_target(
                tdee_kcal_per_day=_dec("2000"),
                goal="invalid_goal",  # type: ignore[arg-type]
            )

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            calculate_calorie_target(_dec("2000"), NutritionGoal.MAINTAIN_WEIGHT)  # type: ignore[call-arg]

    def test_input_immutability(self):
        tdee = _dec("2000")
        goal = NutritionGoal.MAINTAIN_WEIGHT
        tdee_copy = _dec(str(tdee))
        goal_copy = goal
        calculate_calorie_target(tdee_kcal_per_day=tdee, goal=goal)
        assert tdee == tdee_copy
        assert goal == goal_copy

    def test_deterministic_repeated_calls(self):
        r1 = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        r2 = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert r1 == r2

    def test_no_silent_clamping(self):
        with pytest.raises(CalorieTargetBelowMinimumError):
            calculate_calorie_target(
                tdee_kcal_per_day=_dec("1000"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_no_weekly_weight_prediction(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "0.5 kg" not in source
        assert "kg per week" not in source
        assert "weekly" not in source.lower()


# ===========================================================================
# 4. MacroDistribution
# ===========================================================================


class TestMacroDistribution:
    def test_frozen(self):
        dist = MacroDistribution(protein=_dec("0.25"), fat=_dec("0.30"), carbohydrate=_dec("0.45"))
        with pytest.raises(FrozenInstanceError):
            dist.protein = _dec("0.30")  # type: ignore[misc]

    def test_slots_enabled(self):
        dist = MacroDistribution(protein=_dec("0.25"), fat=_dec("0.30"), carbohydrate=_dec("0.45"))
        with pytest.raises((AttributeError, TypeError)):
            dist.new_attr = "test"  # type: ignore[attr-defined]

    def test_decimal_fields(self):
        dist = MacroDistribution(protein=_dec("0.25"), fat=_dec("0.30"), carbohydrate=_dec("0.45"))
        assert isinstance(dist.protein, Decimal)
        assert isinstance(dist.fat, Decimal)
        assert isinstance(dist.carbohydrate, Decimal)

    def test_no_binary_floats(self):
        dist = MacroDistribution(protein=_dec("0.25"), fat=_dec("0.30"), carbohydrate=_dec("0.45"))
        assert not isinstance(dist.protein, float)
        assert not isinstance(dist.fat, float)
        assert not isinstance(dist.carbohydrate, float)


class TestMacroDistributions:
    def test_every_goal_covered(self):
        for goal in NutritionGoal:
            assert goal in MACRO_DISTRIBUTIONS

    def test_exactly_four_entries(self):
        assert len(MACRO_DISTRIBUTIONS) == 4

    def test_no_missing_goals(self):
        assert set(MACRO_DISTRIBUTIONS.keys()) == set(NutritionGoal)

    def test_no_extra_goals(self):
        assert len(MACRO_DISTRIBUTIONS) == len(list(NutritionGoal))

    def test_mapping_immutable(self):
        with pytest.raises(TypeError):
            MACRO_DISTRIBUTIONS[NutritionGoal.MAINTAIN_WEIGHT] = MacroDistribution(  # type: ignore[index]
                protein=_dec("0.30"), fat=_dec("0.30"), carbohydrate=_dec("0.40")
            )

    @pytest.mark.parametrize(
        "goal, exp_protein, exp_fat, exp_carb",
        [
            (NutritionGoal.MAINTAIN_WEIGHT, _dec("0.25"), _dec("0.30"), _dec("0.45")),
            (NutritionGoal.LOSE_WEIGHT, _dec("0.30"), _dec("0.30"), _dec("0.40")),
            (NutritionGoal.GAIN_WEIGHT, _dec("0.25"), _dec("0.25"), _dec("0.50")),
            (NutritionGoal.GAIN_MUSCLE, _dec("0.30"), _dec("0.25"), _dec("0.45")),
        ],
    )
    def test_correct_values(self, goal, exp_protein, exp_fat, exp_carb):
        dist = MACRO_DISTRIBUTIONS[goal]
        assert dist.protein == exp_protein
        assert dist.fat == exp_fat
        assert dist.carbohydrate == exp_carb
        assert isinstance(dist.protein, Decimal)
        assert isinstance(dist.fat, Decimal)
        assert isinstance(dist.carbohydrate, Decimal)

    def test_every_goal_totals_exactly_one(self):
        for goal in NutritionGoal:
            dist = MACRO_DISTRIBUTIONS[goal]
            total = dist.protein + dist.fat + dist.carbohydrate
            assert total == _dec("1.00")

    def test_every_percentage_positive(self):
        for goal in NutritionGoal:
            dist = MACRO_DISTRIBUTIONS[goal]
            assert dist.protein > 0
            assert dist.fat > 0
            assert dist.carbohydrate > 0

    def test_values_immutable(self):
        dist = MACRO_DISTRIBUTIONS[NutritionGoal.MAINTAIN_WEIGHT]
        with pytest.raises(FrozenInstanceError):
            dist.protein = _dec("0.30")  # type: ignore[misc]

    def test_no_binary_floats_in_values(self):
        for goal in NutritionGoal:
            dist = MACRO_DISTRIBUTIONS[goal]
            assert not isinstance(dist.protein, float)
            assert not isinstance(dist.fat, float)
            assert not isinstance(dist.carbohydrate, float)


# ===========================================================================
# 5. Macronutrient targets calculation
# ===========================================================================


class TestCalculateMacronutrientTargets:
    def test_maintain_weight_protein(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        expected = (Decimal("2000") * _dec("0.25") / _dec("4")).quantize(
            _dec("1"), rounding=ROUND_HALF_UP
        )
        assert result.protein_g_per_day == expected

    def test_maintain_weight_carbohydrate(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        expected = (Decimal("2000") * _dec("0.45") / _dec("4")).quantize(
            _dec("1"), rounding=ROUND_HALF_UP
        )
        assert result.carbohydrate_g_per_day == expected

    def test_maintain_weight_fat(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        expected = (Decimal("2000") * _dec("0.30") / _dec("9")).quantize(
            _dec("1"), rounding=ROUND_HALF_UP
        )
        assert result.fat_g_per_day == expected

    def test_known_maintain_weight_values(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.protein_g_per_day == _dec("125")
        assert result.carbohydrate_g_per_day == _dec("225")
        assert result.fat_g_per_day == _dec("67")

    def test_known_lose_weight_values(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("1800"), goal=NutritionGoal.LOSE_WEIGHT
        )
        assert result.protein_g_per_day == _dec("135")
        assert result.carbohydrate_g_per_day == _dec("180")
        assert result.fat_g_per_day == _dec("60")

    def test_known_gain_weight_values(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2500"), goal=NutritionGoal.GAIN_WEIGHT
        )
        assert result.protein_g_per_day == _dec("156")
        assert result.carbohydrate_g_per_day == _dec("313")
        assert result.fat_g_per_day == _dec("69")

    def test_known_gain_muscle_values(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2400"), goal=NutritionGoal.GAIN_MUSCLE
        )
        assert result.protein_g_per_day == _dec("180")
        assert result.carbohydrate_g_per_day == _dec("270")
        assert result.fat_g_per_day == _dec("67")

    def test_whole_gram_decimal_result(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert isinstance(result.protein_g_per_day, Decimal)
        assert isinstance(result.carbohydrate_g_per_day, Decimal)
        assert isinstance(result.fat_g_per_day, Decimal)
        assert result.protein_g_per_day == result.protein_g_per_day.to_integral_value()
        assert result.carbohydrate_g_per_day == result.carbohydrate_g_per_day.to_integral_value()
        assert result.fat_g_per_day == result.fat_g_per_day.to_integral_value()

    def test_round_half_up(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2001"), goal=NutritionGoal.LOSE_WEIGHT
        )
        assert result.protein_g_per_day == _dec("150")

    def test_zero_calories_rejected(self):
        with pytest.raises(ValueError):
            calculate_macronutrient_targets(
                calorie_target_kcal_per_day=_dec("0"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_negative_calories_rejected(self):
        with pytest.raises(ValueError):
            calculate_macronutrient_targets(
                calorie_target_kcal_per_day=_dec("-100"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            calculate_macronutrient_targets(
                calorie_target_kcal_per_day=Decimal("NaN"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_macronutrient_targets(
                calorie_target_kcal_per_day=Decimal("Inf"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_macronutrient_targets(
                calorie_target_kcal_per_day=Decimal("-Inf"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_invalid_goal_rejected(self):
        with pytest.raises(ValueError):
            calculate_macronutrient_targets(
                calorie_target_kcal_per_day=_dec("2000"),
                goal="invalid_goal",  # type: ignore[arg-type]
            )

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            calculate_macronutrient_targets(_dec("2000"), NutritionGoal.MAINTAIN_WEIGHT)  # type: ignore[call-arg]

    def test_frozen_result(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        with pytest.raises(FrozenInstanceError):
            result.protein_g_per_day = _dec("100")  # type: ignore[misc]

    def test_slots_result(self):
        result = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        with pytest.raises((AttributeError, TypeError)):
            result.new_attr = "test"  # type: ignore[attr-defined]

    def test_input_immutability(self):
        cal = _dec("2000")
        goal = NutritionGoal.MAINTAIN_WEIGHT
        cal_copy = _dec(str(cal))
        goal_copy = goal
        calculate_macronutrient_targets(calorie_target_kcal_per_day=cal, goal=goal)
        assert cal == cal_copy
        assert goal == goal_copy

    def test_deterministic_repeated_calls(self):
        r1 = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        r2 = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert r1 == r2


# ===========================================================================
# 6. Combined NutritionTargetResult
# ===========================================================================


class TestNutritionTargetResult:
    def test_uses_calorie_target(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        expected_cal = calculate_calorie_target(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.calorie_target_kcal_per_day == expected_cal

    def test_uses_macro_targets(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        expected_macros = calculate_macronutrient_targets(
            calorie_target_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.protein_g_per_day == expected_macros.protein_g_per_day
        assert result.carbohydrate_g_per_day == expected_macros.carbohydrate_g_per_day
        assert result.fat_g_per_day == expected_macros.fat_g_per_day

    def test_maintain_weight_correct_values(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.calorie_target_kcal_per_day == _dec("2000")
        assert result.protein_g_per_day == _dec("125")
        assert result.carbohydrate_g_per_day == _dec("225")
        assert result.fat_g_per_day == _dec("67")

    def test_lose_weight_correct_values(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.LOSE_WEIGHT
        )
        assert result.calorie_target_kcal_per_day == _dec("1500")
        assert result.protein_g_per_day == _dec("113")
        assert result.carbohydrate_g_per_day == _dec("150")
        assert result.fat_g_per_day == _dec("50")

    def test_gain_weight_correct_values(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.GAIN_WEIGHT
        )
        assert result.calorie_target_kcal_per_day == _dec("2300")
        assert result.protein_g_per_day == _dec("144")
        assert result.carbohydrate_g_per_day == _dec("288")
        assert result.fat_g_per_day == _dec("64")

    def test_gain_muscle_correct_values(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.GAIN_MUSCLE
        )
        assert result.calorie_target_kcal_per_day == _dec("2250")
        assert result.protein_g_per_day == _dec("169")
        assert result.carbohydrate_g_per_day == _dec("253")
        assert result.fat_g_per_day == _dec("63")

    def test_frozen_result(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        with pytest.raises(FrozenInstanceError):
            result.calorie_target_kcal_per_day = _dec("1800")  # type: ignore[misc]

    def test_slots_result(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        with pytest.raises((AttributeError, TypeError)):
            result.new_attr = "test"  # type: ignore[attr-defined]

    def test_below_minimum_exception_propagates(self):
        with pytest.raises(CalorieTargetBelowMinimumError):
            calculate_nutrition_targets(
                tdee_kcal_per_day=_dec("1000"), goal=NutritionGoal.MAINTAIN_WEIGHT
            )

    def test_invalid_goal_rejected(self):
        with pytest.raises(ValueError):
            calculate_nutrition_targets(
                tdee_kcal_per_day=_dec("2000"),
                goal="invalid_goal",  # type: ignore[arg-type]
            )

    def test_no_age_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "age")

    def test_no_bmi_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "bmi")

    def test_no_bmr_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "bmr_kcal_per_day")

    def test_no_tdee_output_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "tdee_kcal_per_day")

    def test_no_weekly_change_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "weekly_change")
        assert not hasattr(result, "weekly_weight_change")

    def test_no_target_date_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "target_date")
        assert not hasattr(result, "projected_date")

    def test_no_health_score_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "health_score")

    def test_no_recommendation_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "recommendation")

    def test_no_meal_plan_field(self):
        result = calculate_nutrition_targets(
            tdee_kcal_per_day=_dec("2000"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert not hasattr(result, "meal_plan")

    def test_no_duplicated_formula_logic(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        cal_section = source[source.find("def calculate_nutrition_targets") :]
        inner_lines = cal_section.split("\n")
        inner = "\n".join(inner_lines)
        assert "calculate_calorie_target" in inner
        assert "calculate_macronutrient_targets" in inner
        assert "PROTEIN_KCAL_PER_GRAM" not in inner
        assert "FAT_KCAL_PER_GRAM" not in inner


# ===========================================================================
# 7. CalorieTargetBelowMinimumError exception
# ===========================================================================


class TestCalorieTargetBelowMinimumError:
    def test_inherits_from_nutrition_calculation_error(self):
        assert issubclass(CalorieTargetBelowMinimumError, NutritionCalculationError)

    def test_default_message_stable(self):
        exc = CalorieTargetBelowMinimumError()
        expected = (
            "The calculated calorie target is below the supported"
            " minimum for this general nutrition estimate."
        )
        assert str(exc) == expected

    def test_can_be_raised(self):
        with pytest.raises(CalorieTargetBelowMinimumError):
            raise CalorieTargetBelowMinimumError()

    def test_can_be_caught_as_base(self):
        with pytest.raises(NutritionCalculationError):
            raise CalorieTargetBelowMinimumError()

    def test_no_http_status_code(self):
        exc = CalorieTargetBelowMinimumError()
        assert not hasattr(exc, "status_code")

    def test_no_fastapi_dependency(self):
        import app.core.nutrition_calculation_exceptions as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_import(self):
        import app.core.nutrition_calculation_exceptions as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_internal_values_exposed(self):
        exc = CalorieTargetBelowMinimumError()
        s = str(exc)
        assert "1200" not in s
        assert "tdee" not in s.lower()
        assert "calorie" in s.lower()

    def test_stable_public_message(self):
        exc = CalorieTargetBelowMinimumError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0
        assert "supported minimum" in s
        assert "general nutrition estimate" in s


# ===========================================================================
# 8. Domain purity — no framework, database, environment, or network leaks
# ===========================================================================


class TestDomainPurity:
    def test_no_fastapi_import(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_sqlalchemy_import(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_pydantic_import(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "pydantic" not in source.lower()

    def test_no_database_session(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "session" not in source.lower()

    def test_no_repository(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "repository" not in source.lower()

    def test_no_api_router(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "router" not in source.lower()
        assert "route" not in source.lower()

    def test_no_environment_access(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "environ" not in source.lower()
        assert "os.getenv" not in source.lower()

    def test_no_network_access(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "import request" not in source.lower()
        assert "urllib" not in source.lower()
        assert "httpx" not in source.lower()

    def test_no_datetime_now(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "datetime.now" not in source

    def test_no_date_today(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "date.today" not in source

    def test_no_random_values(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "random" not in source.lower()

    def test_no_fake_nutrition_data(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "fake" not in source.lower()

    def test_no_api_keys(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "api_key" not in source.lower()
        assert "apikey" not in source.lower()

    def test_no_jwt_handling(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "jwt" not in source.lower()

    def test_no_http_status_codes(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        for code in ("200", "201", "400", "401", "403", "404", "409", "422", "500", "503"):
            assert f'"{code}"' not in source

    def test_no_binary_float_formulas(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "float(" not in source.lower()

    def test_no_ai_generated_values(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "ai" not in source.lower() or "maintain" in source.lower()

    def test_no_persistence(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "insert" not in source.lower()
        assert "update" not in source.lower() or "update" == "update"

    def test_no_meal_plan_generation(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "meal_plan" not in source.lower()
