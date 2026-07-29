from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType

import pytest

from app.core.nutrition_calculation_exceptions import (
    NutritionCalculationError,
    UnsupportedBMRCalculationError,
)
from app.core.nutrition_calculations import (
    ACTIVITY_MULTIPLIERS,
    BMICategory,
    NutritionCalculationResult,
    calculate_age,
    calculate_bmi,
    calculate_bmr,
    calculate_nutrition_metrics,
    calculate_tdee,
    classify_bmi,
)
from app.models.enums import ActivityLevel, BiologicalSex

# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


# ===========================================================================
# 1. Age calculation
# ===========================================================================


class TestCalculateAge:
    def test_birthday_today(self):
        dob = date(1990, 6, 15)
        ref = date(2024, 6, 15)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 34

    def test_birthday_tomorrow(self):
        dob = date(1990, 6, 15)
        ref = date(2024, 6, 14)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 33

    def test_birthday_yesterday(self):
        dob = date(1990, 6, 15)
        ref = date(2024, 6, 16)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 34

    def test_before_birthday(self):
        dob = date(1990, 12, 25)
        ref = date(2024, 6, 15)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 33

    def test_after_birthday(self):
        dob = date(1990, 1, 5)
        ref = date(2024, 6, 15)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 34

    def test_january_birthday(self):
        dob = date(2000, 1, 1)
        ref = date(2024, 1, 1)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 24

    def test_december_birthday(self):
        dob = date(2000, 12, 31)
        ref = date(2024, 12, 31)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 24

    def test_february_29_birth_date_leap_reference(self):
        dob = date(2000, 2, 29)
        ref = date(2024, 2, 29)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 24

    def test_february_29_birth_date_non_leap_reference(self):
        dob = date(2000, 2, 29)
        ref = date(2023, 2, 28)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 23

    def test_february_29_birthday_after_mar_1_non_leap(self):
        dob = date(2000, 2, 29)
        ref = date(2023, 3, 1)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 23

    def test_february_29_birthday_before_feb_28_non_leap(self):
        dob = date(2000, 2, 29)
        ref = date(2023, 2, 27)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 22

    def test_same_date_rejected(self):
        with pytest.raises(ValueError, match="date_of_birth must be earlier"):
            calculate_age(date_of_birth=date(2024, 1, 1), reference_date=date(2024, 1, 1))

    def test_future_birth_date_rejected(self):
        with pytest.raises(ValueError, match="date_of_birth must be earlier"):
            calculate_age(date_of_birth=date(2025, 1, 1), reference_date=date(2024, 1, 1))

    def test_explicit_reference_date_required(self):
        with pytest.raises(TypeError):
            calculate_age(date_of_birth=date(2000, 1, 1))

    def test_no_use_of_date_today(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "date.today()" not in source
        assert "datetime.now()" not in source
        assert "datetime.now" not in source

    def test_deterministic_repeated_calls(self):
        dob = date(1995, 3, 10)
        ref = date(2024, 3, 10)
        r1 = calculate_age(date_of_birth=dob, reference_date=ref)
        r2 = calculate_age(date_of_birth=dob, reference_date=ref)
        assert r1 == r2 == 29

    def test_input_immutability(self):
        dob = date(2000, 1, 1)
        ref = date(2024, 1, 1)
        dob_copy = date(dob.year, dob.month, dob.day)
        ref_copy = date(ref.year, ref.month, ref.day)
        calculate_age(date_of_birth=dob, reference_date=ref)
        assert dob == dob_copy
        assert ref == ref_copy

    def test_keyword_only_args(self):
        with pytest.raises(TypeError):
            calculate_age(date(2000, 1, 1), date(2024, 1, 1))  # type: ignore[call-arg]

    def test_returns_non_negative_int(self):
        dob = date(2023, 1, 1)
        ref = date(2024, 1, 2)
        age = calculate_age(date_of_birth=dob, reference_date=ref)
        assert isinstance(age, int)
        assert age >= 0

    def test_age_zero_newborn(self):
        dob = date(2024, 6, 15)
        ref = date(2024, 12, 25)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 0

    def test_leap_year_feb_28_vs_mar_1(self):
        dob = date(2000, 2, 29)
        ref = date(2024, 2, 28)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 23

    def test_across_century_boundary(self):
        dob = date(1999, 12, 31)
        ref = date(2000, 1, 1)
        assert calculate_age(date_of_birth=dob, reference_date=ref) == 0


# ===========================================================================
# 2. BMI calculation
# ===========================================================================


class TestCalculateBMI:
    def test_known_reference_example(self):
        bmi = calculate_bmi(height_cm=_dec("175"), weight_kg=_dec("70"))
        assert bmi == _dec("22.86")

    def test_known_reference_example_2(self):
        bmi = calculate_bmi(height_cm=_dec("165"), weight_kg=_dec("55"))
        assert bmi == _dec("20.20")

    def test_returns_decimal(self):
        bmi = calculate_bmi(height_cm=_dec("180"), weight_kg=_dec("80"))
        assert isinstance(bmi, Decimal)

    def test_two_decimal_output(self):
        bmi = calculate_bmi(height_cm=_dec("170"), weight_kg=_dec("65"))
        assert bmi.as_tuple().exponent == -2

    def test_round_half_up(self):
        bmi = calculate_bmi(height_cm=_dec("167"), weight_kg=_dec("80.5"))
        assert bmi == _dec("28.86")

    def test_minimum_valid_height(self):
        bmi = calculate_bmi(height_cm=_dec("50"), weight_kg=_dec("10"))
        assert bmi == _dec("40.00")

    def test_maximum_valid_height(self):
        bmi = calculate_bmi(height_cm=_dec("300"), weight_kg=_dec("700"))
        assert bmi == _dec("77.78")

    def test_minimum_valid_weight(self):
        bmi = calculate_bmi(height_cm=_dec("300"), weight_kg=_dec("10"))
        assert bmi == _dec("1.11")

    def test_maximum_valid_weight(self):
        bmi = calculate_bmi(height_cm=_dec("50"), weight_kg=_dec("700"))
        assert bmi == _dec("2800.00")

    def test_below_range_height_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("49.99"), weight_kg=_dec("70"))

    def test_above_range_height_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("300.01"), weight_kg=_dec("70"))

    def test_below_range_weight_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("170"), weight_kg=_dec("9.99"))

    def test_above_range_weight_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("170"), weight_kg=_dec("700.01"))

    def test_zero_height_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("0"), weight_kg=_dec("70"))

    def test_negative_height_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("-10"), weight_kg=_dec("70"))

    def test_zero_weight_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("170"), weight_kg=_dec("0"))

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("170"), weight_kg=_dec("-5"))

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=Decimal("NaN"), weight_kg=_dec("70"))

    def test_positive_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=Decimal("Inf"), weight_kg=_dec("70"))

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=Decimal("-Inf"), weight_kg=_dec("70"))

    def test_no_float_conversion(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "float(" not in source.lower()

    def test_input_immutability(self):
        h = _dec("175")
        w = _dec("70")
        h_copy = Decimal(str(h))
        w_copy = Decimal(str(w))
        calculate_bmi(height_cm=h, weight_kg=w)
        assert h == h_copy
        assert w == w_copy

    def test_deterministic_repeated_calls(self):
        r1 = calculate_bmi(height_cm=_dec("175"), weight_kg=_dec("70"))
        r2 = calculate_bmi(height_cm=_dec("175"), weight_kg=_dec("70"))
        assert r1 == r2

    def test_negative_infinity_weight_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmi(height_cm=_dec("170"), weight_kg=Decimal("-Inf"))


# ===========================================================================
# 3. BMI category
# ===========================================================================


class TestClassifyBMI:
    def test_value_immediately_below_18_5(self):
        assert classify_bmi(bmi=_dec("18.499")) == BMICategory.UNDERWEIGHT

    def test_exact_18_5(self):
        assert classify_bmi(bmi=_dec("18.5")) == BMICategory.HEALTHY_WEIGHT

    def test_value_immediately_below_25(self):
        assert classify_bmi(bmi=_dec("24.999")) == BMICategory.HEALTHY_WEIGHT

    def test_exact_25(self):
        assert classify_bmi(bmi=_dec("25.0")) == BMICategory.OVERWEIGHT

    def test_value_immediately_below_30(self):
        assert classify_bmi(bmi=_dec("29.999")) == BMICategory.OVERWEIGHT

    def test_exact_30(self):
        assert classify_bmi(bmi=_dec("30.0")) == BMICategory.OBESITY

    def test_very_high_positive_bmi(self):
        assert classify_bmi(bmi=_dec("50")) == BMICategory.OBESITY

    def test_very_low_positive_bmi(self):
        assert classify_bmi(bmi=_dec("10")) == BMICategory.UNDERWEIGHT

    def test_zero_rejected(self):
        with pytest.raises(ValueError):
            classify_bmi(bmi=_dec("0"))

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            classify_bmi(bmi=_dec("-1"))

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            classify_bmi(bmi=Decimal("NaN"))

    def test_infinity_rejected(self):
        with pytest.raises(ValueError):
            classify_bmi(bmi=Decimal("Inf"))

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError):
            classify_bmi(bmi=Decimal("-Inf"))

    def test_bmi_category_enum_values(self):
        assert BMICategory.UNDERWEIGHT.value == "underweight"
        assert BMICategory.HEALTHY_WEIGHT.value == "healthy_weight"
        assert BMICategory.OVERWEIGHT.value == "overweight"
        assert BMICategory.OBESITY.value == "obesity"

    def test_bmi_category_enum_members(self):
        assert list(BMICategory) == [
            BMICategory.UNDERWEIGHT,
            BMICategory.HEALTHY_WEIGHT,
            BMICategory.OVERWEIGHT,
            BMICategory.OBESITY,
        ]

    def test_no_diagnostic_language(self):
        for cat in BMICategory:
            v = cat.value
            assert "normal" not in v
            assert "fat" not in v
            assert "obese person" not in v
            assert "unhealthy" not in v
            assert "ideal" not in v

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            classify_bmi(_dec("22"))  # type: ignore[call-arg]

    def test_classification_uses_unrounded_value(self):
        unrounded = _dec("24.9999")
        rounded = unrounded.quantize(_dec("0.01"), rounding=ROUND_HALF_UP)
        assert rounded == _dec("25.00")
        assert classify_bmi(bmi=unrounded) == BMICategory.HEALTHY_WEIGHT


# ===========================================================================
# 4. BMR
# ===========================================================================


class TestCalculateBMR:
    def test_male_formula(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=30,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
        )
        expected = (
            Decimal("10") * _dec("70")
            + Decimal("6.25") * _dec("175")
            - Decimal("5") * _dec("30")
            + Decimal("5")
        )
        expected = expected.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert bmr == expected

    def test_female_formula(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.FEMALE,
            age=30,
            height_cm=_dec("165"),
            weight_kg=_dec("60"),
        )
        expected = (
            Decimal("10") * _dec("60")
            + Decimal("6.25") * _dec("165")
            - Decimal("5") * _dec("30")
            - Decimal("161")
        )
        expected = expected.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert bmr == expected

    def test_male_constant_plus_5(self):
        male_bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=25,
            height_cm=_dec("180"),
            weight_kg=_dec("75"),
        )
        base = (
            Decimal("10") * _dec("75") + Decimal("6.25") * _dec("180") - Decimal("5") * _dec("25")
        )
        expected = (base + Decimal("5")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert male_bmr == expected

    def test_female_constant_minus_161(self):
        female_bmr = calculate_bmr(
            biological_sex=BiologicalSex.FEMALE,
            age=25,
            height_cm=_dec("180"),
            weight_kg=_dec("75"),
        )
        base = (
            Decimal("10") * _dec("75") + Decimal("6.25") * _dec("180") - Decimal("5") * _dec("25")
        )
        expected = (base - Decimal("161")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert female_bmr == expected

    def test_known_values_male(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=30,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
        )
        assert bmr == _dec("1649")  # 700 + 1093.75 - 150 + 5 = 1648.75 -> 1649

    def test_known_values_female(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.FEMALE,
            age=25,
            height_cm=_dec("165"),
            weight_kg=_dec("58"),
        )
        assert bmr == _dec("1325")  # 580 + 1031.25 - 125 - 161 = 1325.25 -> 1325

    def test_correct_decimal_result(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=40,
            height_cm=_dec("170"),
            weight_kg=_dec("80"),
        )
        assert isinstance(bmr, Decimal)

    def test_whole_number_kcal_rounding(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=40,
            height_cm=_dec("170"),
            weight_kg=_dec("80"),
        )
        assert bmr == bmr.to_integral_value()

    def test_round_half_up_behavior(self):
        base = (
            Decimal("10") * _dec("70")
            + Decimal("6.25") * _dec("175")
            - Decimal("5") * _dec("30")
            + Decimal("5")
        )
        male_bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=30,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
        )
        assert male_bmr == base.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    def test_minimum_valid_height_and_weight(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=20,
            height_cm=_dec("50"),
            weight_kg=_dec("10"),
        )
        assert bmr > 0

    def test_maximum_valid_height_and_weight(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=20,
            height_cm=_dec("300"),
            weight_kg=_dec("700"),
        )
        assert bmr > 0

    def test_invalid_height_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmr(
                biological_sex=BiologicalSex.MALE,
                age=30,
                height_cm=_dec("49.99"),
                weight_kg=_dec("70"),
            )

    def test_invalid_weight_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmr(
                biological_sex=BiologicalSex.MALE,
                age=30,
                height_cm=_dec("170"),
                weight_kg=_dec("9.99"),
            )

    def test_age_zero_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmr(
                biological_sex=BiologicalSex.MALE,
                age=0,
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_negative_age_rejected(self):
        with pytest.raises(ValueError):
            calculate_bmr(
                biological_sex=BiologicalSex.MALE,
                age=-5,
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_bool_age_rejected(self):
        with pytest.raises(ValueError, match="age must be an integer"):
            calculate_bmr(
                biological_sex=BiologicalSex.MALE,
                age=True,  # type: ignore[arg-type]
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_float_age_rejected(self):
        with pytest.raises(ValueError, match="age must be an integer"):
            calculate_bmr(
                biological_sex=BiologicalSex.MALE,
                age=30.5,  # type: ignore[arg-type]
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_other_rejected_safely(self):
        with pytest.raises(UnsupportedBMRCalculationError):
            calculate_bmr(
                biological_sex=BiologicalSex.OTHER,
                age=30,
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_prefer_not_to_say_rejected_safely(self):
        with pytest.raises(UnsupportedBMRCalculationError):
            calculate_bmr(
                biological_sex=BiologicalSex.PREFER_NOT_TO_SAY,
                age=30,
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_other_exception_inherits_correctly(self):
        with pytest.raises(NutritionCalculationError):
            calculate_bmr(
                biological_sex=BiologicalSex.OTHER,
                age=30,
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_no_guessed_constant(self):
        with pytest.raises(UnsupportedBMRCalculationError):
            calculate_bmr(
                biological_sex=BiologicalSex.OTHER,
                age=30,
                height_cm=_dec("170"),
                weight_kg=_dec("70"),
            )

    def test_deterministic_repeated_calls(self):
        r1 = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=30,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
        )
        r2 = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=30,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
        )
        assert r1 == r2

    def test_input_immutability(self):
        h = _dec("175")
        w = _dec("70")
        h_copy = Decimal(str(h))
        w_copy = Decimal(str(w))
        calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=30,
            height_cm=h,
            weight_kg=w,
        )
        assert h == h_copy
        assert w == w_copy

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            calculate_bmr(  # type: ignore[call-arg]
                BiologicalSex.MALE, 30, _dec("170"), _dec("70")
            )

    def test_male_age_1(self):
        bmr = calculate_bmr(
            biological_sex=BiologicalSex.MALE,
            age=1,
            height_cm=_dec("50"),
            weight_kg=_dec("10"),
        )
        assert bmr > 0


# ===========================================================================
# 5. Activity multipliers
# ===========================================================================


class TestActivityMultipliers:
    def test_all_five_values_exact(self):
        assert ACTIVITY_MULTIPLIERS[ActivityLevel.SEDENTARY] == _dec("1.2")
        assert ACTIVITY_MULTIPLIERS[ActivityLevel.LIGHTLY_ACTIVE] == _dec("1.375")
        assert ACTIVITY_MULTIPLIERS[ActivityLevel.MODERATELY_ACTIVE] == _dec("1.55")
        assert ACTIVITY_MULTIPLIERS[ActivityLevel.VERY_ACTIVE] == _dec("1.725")
        assert ACTIVITY_MULTIPLIERS[ActivityLevel.EXTRA_ACTIVE] == _dec("1.9")

    def test_decimal_values_only(self):
        for v in ACTIVITY_MULTIPLIERS.values():
            assert isinstance(v, Decimal)

    def test_every_activity_level_member_covered(self):
        for level in ActivityLevel:
            assert level in ACTIVITY_MULTIPLIERS

    def test_no_missing_enum_members(self):
        assert len(ACTIVITY_MULTIPLIERS) == len(list(ActivityLevel))

    def test_no_extra_keys(self):
        assert set(ACTIVITY_MULTIPLIERS.keys()) == set(ActivityLevel)

    def test_mapping_immutable(self):
        with pytest.raises(TypeError):
            ACTIVITY_MULTIPLIERS[ActivityLevel.SEDENTARY] = _dec("1.0")  # type: ignore[index]

    def test_no_binary_floats(self):
        for v in ACTIVITY_MULTIPLIERS.values():
            assert isinstance(v, Decimal)

    def test_is_mapping_proxy_type(self):
        assert isinstance(ACTIVITY_MULTIPLIERS, MappingProxyType)


# ===========================================================================
# 6. TDEE
# ===========================================================================


class TestCalculateTDEE:
    def test_known_sedentary_result(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.SEDENTARY)
        assert tdee == _dec("1920")

    def test_known_lightly_active_result(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.LIGHTLY_ACTIVE)
        assert tdee == _dec("2200")

    def test_known_moderately_active_result(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.MODERATELY_ACTIVE)
        assert tdee == _dec("2480")

    def test_known_very_active_result(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.VERY_ACTIVE)
        assert tdee == _dec("2760")

    def test_known_extra_active_result(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.EXTRA_ACTIVE)
        assert tdee == _dec("3040")

    def test_decimal_return_type(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.MODERATELY_ACTIVE)
        assert isinstance(tdee, Decimal)

    def test_whole_kcal_rounding(self):
        tdee = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.MODERATELY_ACTIVE)
        assert tdee == tdee.to_integral_value()

    def test_round_half_up(self):
        tdee = calculate_tdee(bmr=_dec("1601"), activity_level=ActivityLevel.SEDENTARY)
        assert tdee == _dec("1921")

    def test_zero_bmr_rejected(self):
        with pytest.raises(ValueError):
            calculate_tdee(bmr=_dec("0"), activity_level=ActivityLevel.SEDENTARY)

    def test_negative_bmr_rejected(self):
        with pytest.raises(ValueError):
            calculate_tdee(bmr=_dec("-100"), activity_level=ActivityLevel.SEDENTARY)

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            calculate_tdee(bmr=Decimal("NaN"), activity_level=ActivityLevel.SEDENTARY)

    def test_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_tdee(bmr=Decimal("Inf"), activity_level=ActivityLevel.SEDENTARY)

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError):
            calculate_tdee(bmr=Decimal("-Inf"), activity_level=ActivityLevel.SEDENTARY)

    def test_invalid_activity_level_rejected(self):
        with pytest.raises(ValueError):
            calculate_tdee(bmr=_dec("1600"), activity_level="invalid_level")  # type: ignore[arg-type]

    def test_deterministic_repeated_calls(self):
        r1 = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.MODERATELY_ACTIVE)
        r2 = calculate_tdee(bmr=_dec("1600"), activity_level=ActivityLevel.MODERATELY_ACTIVE)
        assert r1 == r2

    def test_input_immutability(self):
        b = _dec("1600")
        b_copy = Decimal(str(b))
        lvl = ActivityLevel.MODERATELY_ACTIVE
        calculate_tdee(bmr=b, activity_level=lvl)
        assert b == b_copy

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            calculate_tdee(_dec("1600"), ActivityLevel.SEDENTARY)  # type: ignore[call-arg]


# ===========================================================================
# 7. Combined result
# ===========================================================================


class TestNutritionCalculationResult:
    def test_frozen_dataclass(self):
        result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1664"),
            tdee_kcal_per_day=_dec("2579"),
        )
        with pytest.raises(AttributeError):
            result.age = 31  # type: ignore[misc]

    def test_all_fields(self):
        dob = date(1990, 6, 15)
        ref = date(2024, 6, 15)
        result = calculate_nutrition_metrics(
            date_of_birth=dob,
            reference_date=ref,
            biological_sex=BiologicalSex.MALE,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
        )
        assert isinstance(result, NutritionCalculationResult)
        assert result.age == 34
        assert result.bmi == _dec("22.86")
        assert result.bmi_category == BMICategory.HEALTHY_WEIGHT
        assert result.bmr_kcal_per_day > 0
        assert result.tdee_kcal_per_day > 0

    def test_uses_unrounded_bmi_for_category(self):
        dob = date(1990, 1, 1)
        ref = date(2024, 1, 1)
        h = _dec("167")
        w = _dec("69.7")
        unrounded = w / ((h / _dec("100")) ** 2)
        rounded = unrounded.quantize(_dec("0.01"), rounding=ROUND_HALF_UP)
        result = calculate_nutrition_metrics(
            date_of_birth=dob,
            reference_date=ref,
            biological_sex=BiologicalSex.MALE,
            height_cm=h,
            weight_kg=w,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
        )
        assert result.bmi == rounded
        cat_from_unrounded = classify_bmi(bmi=unrounded)
        assert result.bmi_category == cat_from_unrounded

    def test_immutable(self):
        dob = date(1990, 6, 15)
        ref = date(2024, 6, 15)
        result = calculate_nutrition_metrics(
            date_of_birth=dob,
            reference_date=ref,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=_dec("165"),
            weight_kg=_dec("60"),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
        )
        with pytest.raises(AttributeError):
            result.age = 40  # type: ignore[misc]

    def test_deterministic(self):
        r1 = calculate_nutrition_metrics(
            date_of_birth=date(1990, 6, 15),
            reference_date=date(2024, 6, 15),
            biological_sex=BiologicalSex.MALE,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
        )
        r2 = calculate_nutrition_metrics(
            date_of_birth=date(1990, 6, 15),
            reference_date=date(2024, 6, 15),
            biological_sex=BiologicalSex.MALE,
            height_cm=_dec("175"),
            weight_kg=_dec("70"),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
        )
        assert r1 == r2


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

    def test_no_service(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "class.*[Ss]ervice" not in source

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

    def test_no_hidden_global_mutable_state(self):
        import app.core.nutrition_calculations as mod

        source = open(mod.__file__).read()
        assert "global" not in source

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
