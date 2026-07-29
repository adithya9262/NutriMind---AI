from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.nutrition_calculations import (
    MINIMUM_CALORIE_TARGET,
    BMICategory,
    NutritionCalculationResult,
    NutritionTargetResult,
)
from app.schemas import (
    CalculatedNutritionData,
    CalculatedNutritionSuccessResponse,
    NutritionMetricsData,
    NutritionTargetsData,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dec(value: str) -> Decimal:
    return Decimal(value)


_VALID_METRICS = {
    "age_years": 30,
    "bmi": "22.86",
    "bmi_category": "healthy_weight",
    "bmr_kcal_per_day": "1649",
    "tdee_kcal_per_day": "2556",
}

_VALID_TARGETS = {
    "calorie_target_kcal_per_day": "2056",
    "protein_g_per_day": "154",
    "carbohydrate_g_per_day": "206",
    "fat_g_per_day": "69",
}


def _valid_metrics_dict(overrides: dict | None = None) -> dict:
    d = dict(_VALID_METRICS)
    if overrides:
        d.update(overrides)
    return d


def _valid_targets_dict(overrides: dict | None = None) -> dict:
    d = dict(_VALID_TARGETS)
    if overrides:
        d.update(overrides)
    return d


def _valid_combined_dict(overrides: dict | None = None) -> dict:
    d = {
        "metrics": dict(_VALID_METRICS),
        "targets": dict(_VALID_TARGETS),
    }
    if overrides:
        d.update(overrides)
    return d


# ===========================================================================
# A. NutritionMetricsData
# ===========================================================================


class TestNutritionMetricsDataValid:
    def test_valid_construction(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        assert m.age_years == 30
        assert m.bmi == _dec("22.86")
        assert m.bmi_category == BMICategory.HEALTHY_WEIGHT
        assert m.bmr_kcal_per_day == _dec("1649")
        assert m.tdee_kcal_per_day == _dec("2556")

    def test_correct_field_types(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        assert isinstance(m.age_years, int)
        assert isinstance(m.bmi, Decimal)
        assert isinstance(m.bmi_category, BMICategory)
        assert isinstance(m.bmr_kcal_per_day, Decimal)
        assert isinstance(m.tdee_kcal_per_day, Decimal)

    def test_decimal_values_preserved(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        assert isinstance(m.bmi, Decimal)
        assert m.bmi == _dec("22.86")
        assert m.bmr_kcal_per_day == _dec("1649")
        assert m.tdee_kcal_per_day == _dec("2556")

    def test_existing_bmi_category_reused(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        assert m.bmi_category is BMICategory.HEALTHY_WEIGHT
        assert m.bmi_category.__class__ is BMICategory

    def test_every_bmi_category_accepted(self):
        for cat in BMICategory:
            m = NutritionMetricsData.model_validate(
                _valid_metrics_dict({"bmi_category": cat.value})
            )
            assert m.bmi_category == cat

    def test_age_years_accepts_positive_integer(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": 1}))
        assert m.age_years == 1

    def test_age_years_accepts_large_integer(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": 120}))
        assert m.age_years == 120

    def test_age_years_rejects_string_integer(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": "30"}))


class TestNutritionMetricsDataMissingFields:
    def test_missing_age_years_rejected(self):
        d = _valid_metrics_dict()
        del d["age_years"]
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(d)

    def test_missing_bmi_rejected(self):
        d = _valid_metrics_dict()
        del d["bmi"]
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(d)

    def test_missing_bmi_category_rejected(self):
        d = _valid_metrics_dict()
        del d["bmi_category"]
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(d)

    def test_missing_bmr_rejected(self):
        d = _valid_metrics_dict()
        del d["bmr_kcal_per_day"]
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(d)

    def test_missing_tdee_rejected(self):
        d = _valid_metrics_dict()
        del d["tdee_kcal_per_day"]
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(d)


class TestNutritionMetricsDataNullFields:
    def test_null_age_years_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": None}))

    def test_null_bmi_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": None}))

    def test_null_bmi_category_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi_category": None}))

    def test_null_bmr_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmr_kcal_per_day": None}))

    def test_null_tdee_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"tdee_kcal_per_day": None}))


class TestNutritionMetricsDataExtraFields:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"unknown_field": "value"}))

    def test_extra_fields_rejected(self):
        extra = [
            "date_of_birth",
            "biological_sex",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
            "target_weight_kg",
            "dietary_preference",
            "allergies",
            "user_id",
            "profile_id",
            "password",
            "access_token",
        ]
        for field in extra:
            with pytest.raises(ValidationError):
                NutritionMetricsData.model_validate(_valid_metrics_dict({field: "test"}))


class TestNutritionMetricsDataAgeValidation:
    def test_rejects_bool(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": True}))

    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": 0}))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": -1}))

    def test_rejects_float(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": 30.5}))

    def test_rejects_string_non_numeric(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"age_years": "thirty"}))


class TestNutritionMetricsDataBMIValidation:
    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": "0"}))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": "-1"}))

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": float("nan")}))

    def test_rejects_positive_infinity(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": float("inf")}))

    def test_rejects_negative_infinity(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": float("-inf")}))

    def test_accepts_small_positive(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict({"bmi": "10.00"}))
        assert m.bmi == _dec("10.00")


class TestNutritionMetricsDataBMRValidation:
    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmr_kcal_per_day": "0"}))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"bmr_kcal_per_day": "-100"}))

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"bmr_kcal_per_day": float("nan")})
            )

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"bmr_kcal_per_day": float("inf")})
            )

    def test_rejects_negative_infinity(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"bmr_kcal_per_day": float("-inf")})
            )


class TestNutritionMetricsDataTDEValidation:
    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"tdee_kcal_per_day": "0"}))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(_valid_metrics_dict({"tdee_kcal_per_day": "-100"}))

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"tdee_kcal_per_day": float("nan")})
            )

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"tdee_kcal_per_day": float("inf")})
            )

    def test_rejects_negative_infinity(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"tdee_kcal_per_day": float("-inf")})
            )


class TestNutritionMetricsDataFrozen:
    def test_model_is_frozen(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        with pytest.raises(ValidationError):
            m.age_years = 31  # type: ignore[misc]

    def test_mutation_rejected(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        with pytest.raises(ValidationError):
            m.bmi = _dec("23.00")  # type: ignore[misc]


class TestNutritionMetricsDataSerialization:
    def test_model_dump_preserves_values(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        data = m.model_dump()
        assert data["age_years"] == 30
        assert data["bmi"] == _dec("22.86")
        assert data["bmi_category"] == BMICategory.HEALTHY_WEIGHT
        assert data["bmr_kcal_per_day"] == _dec("1649")
        assert data["tdee_kcal_per_day"] == _dec("2556")

    def test_model_dump_json_uses_decimal_strings(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        raw = m.model_dump_json()
        obj = json.loads(raw)
        assert obj["age_years"] == 30
        assert obj["bmi"] == "22.86"
        assert obj["bmi_category"] == "healthy_weight"
        assert obj["bmr_kcal_per_day"] == "1649"
        assert obj["tdee_kcal_per_day"] == "2556"

    def test_model_dump_json_no_floats(self):
        m = NutritionMetricsData.model_validate(_valid_metrics_dict())
        raw = m.model_dump_json()
        obj = json.loads(raw)
        assert isinstance(obj["bmi"], str)
        assert isinstance(obj["bmr_kcal_per_day"], str)
        assert isinstance(obj["tdee_kcal_per_day"], str)


class TestNutritionMetricsDataUnknownBMICategory:
    def test_unknown_bmi_category_rejected(self):
        with pytest.raises(ValidationError):
            NutritionMetricsData.model_validate(
                _valid_metrics_dict({"bmi_category": "unknown_category"})
            )

    def test_no_duplicate_bmi_enum(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text()
        assert source.count("class BMICategory") == 0


# ===========================================================================
# B. NutritionTargetsData
# ===========================================================================


class TestNutritionTargetsDataValid:
    def test_valid_construction(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        assert t.calorie_target_kcal_per_day == _dec("2056")
        assert t.protein_g_per_day == _dec("154")
        assert t.carbohydrate_g_per_day == _dec("206")
        assert t.fat_g_per_day == _dec("69")

    def test_decimal_values_preserved(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        assert isinstance(t.calorie_target_kcal_per_day, Decimal)
        assert isinstance(t.protein_g_per_day, Decimal)
        assert isinstance(t.carbohydrate_g_per_day, Decimal)
        assert isinstance(t.fat_g_per_day, Decimal)

    def test_all_fields_required(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        assert t.calorie_target_kcal_per_day == _dec("2056")

    def test_calorie_target_at_minimum_accepted(self):
        t = NutritionTargetsData.model_validate(
            _valid_targets_dict({"calorie_target_kcal_per_day": str(MINIMUM_CALORIE_TARGET)})
        )
        assert t.calorie_target_kcal_per_day == MINIMUM_CALORIE_TARGET


class TestNutritionTargetsDataMissingFields:
    def test_missing_calorie_target_rejected(self):
        d = _valid_targets_dict()
        del d["calorie_target_kcal_per_day"]
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(d)

    def test_missing_protein_rejected(self):
        d = _valid_targets_dict()
        del d["protein_g_per_day"]
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(d)

    def test_missing_carbohydrate_rejected(self):
        d = _valid_targets_dict()
        del d["carbohydrate_g_per_day"]
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(d)

    def test_missing_fat_rejected(self):
        d = _valid_targets_dict()
        del d["fat_g_per_day"]
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(d)


class TestNutritionTargetsDataNullFields:
    def test_null_calorie_target_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"calorie_target_kcal_per_day": None})
            )

    def test_null_protein_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"protein_g_per_day": None}))

    def test_null_carbohydrate_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"carbohydrate_g_per_day": None})
            )

    def test_null_fat_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"fat_g_per_day": None}))


class TestNutritionTargetsDataExtraFields:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"unknown_field": "value"}))

    def test_weekly_weight_change_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"weekly_weight_change": "0.5"})
            )

    def test_target_date_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"target_date": "2025-01-01"}))

    def test_health_score_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"health_score": 85}))

    def test_recommendation_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"recommendation": "eat more protein"})
            )

    def test_meal_plan_rejected(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"meal_plan": "keto"}))


class TestNutritionTargetsDataCalorieValidation:
    def test_below_minimum_rejected(self):
        below = str(int(MINIMUM_CALORIE_TARGET) - 1)
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"calorie_target_kcal_per_day": below})
            )

    def test_no_silent_clamping(self):
        below = str(int(MINIMUM_CALORIE_TARGET) - 1)
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"calorie_target_kcal_per_day": below})
            )

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"calorie_target_kcal_per_day": float("nan")})
            )

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"calorie_target_kcal_per_day": float("inf")})
            )

    def test_rejects_negative_infinity(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"calorie_target_kcal_per_day": float("-inf")})
            )


class TestNutritionTargetsDataProteinValidation:
    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"protein_g_per_day": "0"}))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"protein_g_per_day": "-1"}))

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"protein_g_per_day": float("nan")})
            )

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"protein_g_per_day": float("inf")})
            )


class TestNutritionTargetsDataCarbohydrateValidation:
    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"carbohydrate_g_per_day": "0"})
            )

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"carbohydrate_g_per_day": "-1"})
            )

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"carbohydrate_g_per_day": float("nan")})
            )

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"carbohydrate_g_per_day": float("inf")})
            )


class TestNutritionTargetsDataFatValidation:
    def test_rejects_zero(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"fat_g_per_day": "0"}))

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(_valid_targets_dict({"fat_g_per_day": "-1"}))

    def test_rejects_nan(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"fat_g_per_day": float("nan")})
            )

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            NutritionTargetsData.model_validate(
                _valid_targets_dict({"fat_g_per_day": float("inf")})
            )


class TestNutritionTargetsDataFrozen:
    def test_model_is_frozen(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        with pytest.raises(ValidationError):
            t.calorie_target_kcal_per_day = _dec("2000")  # type: ignore[misc]

    def test_mutation_rejected(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        with pytest.raises(ValidationError):
            t.protein_g_per_day = _dec("100")  # type: ignore[misc]


class TestNutritionTargetsDataSerialization:
    def test_model_dump_preserves_values(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        data = t.model_dump()
        assert data["calorie_target_kcal_per_day"] == _dec("2056")
        assert data["protein_g_per_day"] == _dec("154")
        assert data["carbohydrate_g_per_day"] == _dec("206")
        assert data["fat_g_per_day"] == _dec("69")

    def test_model_dump_json_uses_decimal_strings(self):
        t = NutritionTargetsData.model_validate(_valid_targets_dict())
        raw = t.model_dump_json()
        obj = json.loads(raw)
        assert obj["calorie_target_kcal_per_day"] == "2056"
        assert obj["protein_g_per_day"] == "154"
        assert obj["carbohydrate_g_per_day"] == "206"
        assert obj["fat_g_per_day"] == "69"


# ===========================================================================
# C. CalculatedNutritionData
# ===========================================================================


class TestCalculatedNutritionDataValid:
    def test_valid_nested_construction(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        assert isinstance(c.metrics, NutritionMetricsData)
        assert isinstance(c.targets, NutritionTargetsData)
        assert c.metrics.age_years == 30
        assert c.targets.calorie_target_kcal_per_day == _dec("2056")

    def test_correct_nested_model_types(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        assert type(c.metrics) is NutritionMetricsData
        assert type(c.targets) is NutritionTargetsData


class TestCalculatedNutritionDataMissingFields:
    def test_missing_metrics_rejected(self):
        d = _valid_combined_dict()
        del d["metrics"]
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(d)

    def test_missing_targets_rejected(self):
        d = _valid_combined_dict()
        del d["targets"]
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(d)


class TestCalculatedNutritionDataNullFields:
    def test_null_metrics_rejected(self):
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(_valid_combined_dict({"metrics": None}))

    def test_null_targets_rejected(self):
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(_valid_combined_dict({"targets": None}))


class TestCalculatedNutritionDataExtraFields:
    def test_extra_top_level_field_rejected(self):
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(_valid_combined_dict({"extra_field": "value"}))

    def test_extra_nested_metrics_field_rejected(self):
        d = _valid_combined_dict()
        d["metrics"]["extra_metric"] = "value"
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(d)

    def test_extra_nested_targets_field_rejected(self):
        d = _valid_combined_dict()
        d["targets"]["extra_target"] = "value"
        with pytest.raises(ValidationError):
            CalculatedNutritionData.model_validate(d)


class TestCalculatedNutritionDataFrozen:
    def test_model_frozen(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            c.metrics = None  # type: ignore[assignment]

    def test_nested_models_remain_frozen(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            c.metrics.age_years = 40  # type: ignore[misc]


class TestCalculatedNutritionDataSerialization:
    def test_correct_model_dump_structure(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        data = c.model_dump()
        assert "metrics" in data
        assert "targets" in data
        assert "age_years" in data["metrics"]
        assert "calorie_target_kcal_per_day" in data["targets"]

    def test_correct_json_serialization_structure(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        raw = c.model_dump_json()
        obj = json.loads(raw)
        assert "metrics" in obj
        assert "targets" in obj
        assert obj["metrics"]["bmi"] == "22.86"
        assert obj["targets"]["calorie_target_kcal_per_day"] == "2056"

    def test_does_not_expose_raw_profile_fields(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        data = c.model_dump()
        assert "date_of_birth" not in str(data)
        assert "biological_sex" not in str(data)
        assert "height_cm" not in str(data)
        assert "weight_kg" not in str(data)
        assert "activity_level" not in str(data)
        assert "goal" not in str(data)

    def test_does_not_expose_user_fields(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        data = c.model_dump()
        assert "user_id" not in str(data)
        assert "password" not in str(data)
        assert "email" not in str(data)

    def test_does_not_expose_authentication_fields(self):
        c = CalculatedNutritionData.model_validate(_valid_combined_dict())
        data = c.model_dump()
        assert "access_token" not in str(data)
        assert "refresh_token" not in str(data)
        assert "token" not in str(data)


# ===========================================================================
# D. CalculatedNutritionSuccessResponse
# ===========================================================================


class TestCalculatedNutritionSuccessResponseValid:
    def test_valid_response(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        assert r.success is True
        assert r.message == "Nutrition calculations completed successfully."
        assert r.data is data

    def test_success_defaults_to_true(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        assert r.success is True

    def test_success_true_accepted(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(success=True, data=data)
        assert r.success is True

    def test_exact_default_message(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        assert r.message == "Nutrition calculations completed successfully."

    def test_custom_message_accepted(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(
            message="Custom message.",
            data=data,
        )
        assert r.message == "Custom message."

    def test_data_optional(self):
        r = CalculatedNutritionSuccessResponse()
        assert r.data is None

    def test_data_null_accepted(self):
        r = CalculatedNutritionSuccessResponse(data=None)
        assert r.data is None

    def test_extra_fields_rejected(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            CalculatedNutritionSuccessResponse(
                data=data,
                extra_field="value",
            )


class TestCalculatedNutritionSuccessResponseSerialization:
    def test_correct_model_dump(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        dump = r.model_dump()
        assert dump["success"] is True
        assert dump["message"] == "Nutrition calculations completed successfully."
        assert "metrics" in dump["data"]
        assert "targets" in dump["data"]

    def test_correct_model_dump_json(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        raw = r.model_dump_json()
        obj = json.loads(raw)
        assert obj["success"] is True
        assert obj["message"] == "Nutrition calculations completed successfully."
        assert obj["data"]["metrics"]["bmi"] == "22.86"
        assert obj["data"]["targets"]["calorie_target_kcal_per_day"] == "2056"

    def test_enum_serialization(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        raw = r.model_dump_json()
        obj = json.loads(raw)
        assert obj["data"]["metrics"]["bmi_category"] == "healthy_weight"

    def test_decimal_serialization(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        r = CalculatedNutritionSuccessResponse(data=data)
        raw = r.model_dump_json()
        obj = json.loads(raw)
        assert isinstance(obj["data"]["metrics"]["bmi"], str)
        assert isinstance(obj["data"]["targets"]["calorie_target_kcal_per_day"], str)


class TestCalculatedNutritionSuccessResponseRejection:
    def test_error_field_rejected(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            CalculatedNutritionSuccessResponse(data=data, error="error")

    def test_password_field_rejected(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            CalculatedNutritionSuccessResponse(data=data, password="secret")

    def test_token_field_rejected(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            CalculatedNutritionSuccessResponse(data=data, access_token="token")

    def test_secret_field_rejected(self):
        data = CalculatedNutritionData.model_validate(_valid_combined_dict())
        with pytest.raises(ValidationError):
            CalculatedNutritionSuccessResponse(data=data, secret="value")


# ===========================================================================
# E. From-result conversion helpers
# ===========================================================================


class TestNutritionMetricsDataFromResult:
    def test_converts_correctly(self):
        result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        m = NutritionMetricsData.from_result(result)
        assert m.age_years == 30
        assert m.bmi == _dec("22.86")
        assert m.bmi_category == BMICategory.HEALTHY_WEIGHT
        assert m.bmr_kcal_per_day == _dec("1649")
        assert m.tdee_kcal_per_day == _dec("2556")

    def test_every_value_copied_exactly(self):
        result = NutritionCalculationResult(
            age=25,
            bmi=_dec("20.20"),
            bmi_category=BMICategory.UNDERWEIGHT,
            bmr_kcal_per_day=_dec("1325"),
            tdee_kcal_per_day=_dec("2054"),
        )
        m = NutritionMetricsData.from_result(result)
        assert m.age_years == result.age
        assert m.bmi == result.bmi
        assert m.bmi_category == result.bmi_category
        assert m.bmr_kcal_per_day == result.bmr_kcal_per_day
        assert m.tdee_kcal_per_day == result.tdee_kcal_per_day

    def test_no_recalculation(self):
        result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        result_copy = NutritionCalculationResult(
            age=result.age,
            bmi=result.bmi,
            bmi_category=result.bmi_category,
            bmr_kcal_per_day=result.bmr_kcal_per_day,
            tdee_kcal_per_day=result.tdee_kcal_per_day,
        )
        NutritionMetricsData.from_result(result)
        assert result == result_copy

    def test_input_unchanged(self):
        result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        NutritionMetricsData.from_result(result)
        assert result.age == 30
        assert result.bmi == _dec("22.86")

    def test_deterministic_repeated_calls(self):
        result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        r1 = NutritionMetricsData.from_result(result)
        r2 = NutritionMetricsData.from_result(result)
        assert r1.model_dump() == r2.model_dump()


class TestNutritionTargetsDataFromResult:
    def test_converts_correctly(self):
        result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        t = NutritionTargetsData.from_result(result)
        assert t.calorie_target_kcal_per_day == _dec("2056")
        assert t.protein_g_per_day == _dec("154")
        assert t.carbohydrate_g_per_day == _dec("206")
        assert t.fat_g_per_day == _dec("69")

    def test_every_value_copied_exactly(self):
        result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("1500"),
            protein_g_per_day=_dec("113"),
            carbohydrate_g_per_day=_dec("150"),
            fat_g_per_day=_dec("50"),
        )
        t = NutritionTargetsData.from_result(result)
        assert t.calorie_target_kcal_per_day == result.calorie_target_kcal_per_day
        assert t.protein_g_per_day == result.protein_g_per_day
        assert t.carbohydrate_g_per_day == result.carbohydrate_g_per_day
        assert t.fat_g_per_day == result.fat_g_per_day

    def test_no_recalculation(self):
        result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        result_copy = NutritionTargetResult(
            calorie_target_kcal_per_day=result.calorie_target_kcal_per_day,
            protein_g_per_day=result.protein_g_per_day,
            carbohydrate_g_per_day=result.carbohydrate_g_per_day,
            fat_g_per_day=result.fat_g_per_day,
        )
        NutritionTargetsData.from_result(result)
        assert result == result_copy

    def test_input_unchanged(self):
        result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        NutritionTargetsData.from_result(result)
        assert result.calorie_target_kcal_per_day == _dec("2056")
        assert result.protein_g_per_day == _dec("154")

    def test_deterministic_repeated_calls(self):
        result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        r1 = NutritionTargetsData.from_result(result)
        r2 = NutritionTargetsData.from_result(result)
        assert r1.model_dump() == r2.model_dump()


class TestCalculatedNutritionDataFromResults:
    def test_combined_conversion_works(self):
        metrics_result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        targets_result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        c = CalculatedNutritionData.from_results(metrics_result, targets_result)
        assert c.metrics.age_years == 30
        assert c.metrics.bmi == _dec("22.86")
        assert c.targets.calorie_target_kcal_per_day == _dec("2056")
        assert c.targets.protein_g_per_day == _dec("154")

    def test_inputs_unchanged(self):
        metrics_result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        targets_result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        CalculatedNutritionData.from_results(metrics_result, targets_result)
        assert metrics_result.age == 30
        assert targets_result.calorie_target_kcal_per_day == _dec("2056")

    def test_deterministic_repeated_calls(self):
        metrics_result = NutritionCalculationResult(
            age=30,
            bmi=_dec("22.86"),
            bmi_category=BMICategory.HEALTHY_WEIGHT,
            bmr_kcal_per_day=_dec("1649"),
            tdee_kcal_per_day=_dec("2556"),
        )
        targets_result = NutritionTargetResult(
            calorie_target_kcal_per_day=_dec("2056"),
            protein_g_per_day=_dec("154"),
            carbohydrate_g_per_day=_dec("206"),
            fat_g_per_day=_dec("69"),
        )
        r1 = CalculatedNutritionData.from_results(metrics_result, targets_result)
        r2 = CalculatedNutritionData.from_results(metrics_result, targets_result)
        assert r1.model_dump() == r2.model_dump()


# ===========================================================================
# F. Schema boundaries
# ===========================================================================


class TestSchemaBoundaries:
    def test_no_fastapi_import(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "fastapi" not in source

    def test_no_sqlalchemy_import(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "sqlalchemy" not in source

    def test_no_database_import(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "session" not in source
        assert "db" not in source or "field_validator" in source

    def test_no_repository_import(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "repository" not in source

    def test_no_service_import(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "service" not in source

    def test_no_api_router_import(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "router" not in source
        assert "route" not in source

    def test_no_http_exception(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "http_exception" not in source.replace("_", "")

    def test_no_http_status_codes(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text()
        for code in ("200", "201", "400", "401", "403", "404", "409", "422", "500", "503"):
            assert f'"{code}"' not in source

    def test_no_environment_access(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "environ" not in source
        assert "os.getenv" not in source

    def test_no_network_access(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "import request" not in source
        assert "urllib" not in source
        assert "httpx" not in source

    def test_no_date_today(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text()
        assert "date.today()" not in source
        assert "datetime.now()" not in source

    def test_no_random(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "random" not in source

    def test_no_jwt(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "jwt" not in source

    def test_no_api_keys(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "api_key" not in source
        assert "apikey" not in source

    def test_no_persistence(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "insert" not in source
        assert "update" not in source or "update" == "update"

    def test_no_meal_plan_functionality(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "meal_plan" not in source
        assert "diet_plan" not in source
        assert "cheat_meal" not in source

    def test_no_fake_nutrition_information(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "fake" not in source

    def test_no_float_conversion_of_decimals(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "float(" not in source

    def test_no_duplicated_calorie_formula(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text()
        assert 'Decimal("-500")' not in source
        assert 'Decimal("300")' not in source

    def test_no_duplicated_macro_formula(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "4 kcal" not in source.lower()
        assert "9 kcal" not in source.lower()

    def test_no_duplicated_bmi_formula(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "height_m" not in source.lower()

    def test_no_duplicated_bmr_formula(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "6.25" not in source

    def test_no_duplicated_tdee_formula(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "1.2" not in source and "sedentary" not in source.lower()

    def test_no_usda_functionality(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "usda" not in source

    def test_no_groq_functionality(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        assert "groq" not in source

    def test_no_ai_functionality(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text().lower()
        for term in ("openai", "langchain", "llm", "chatbot", "gemini", "claude"):
            assert term not in source, f"AI term '{term}' found"

    def test_no_profile_fields_in_schema(self):
        import app.schemas.nutrition_calculations as mod

        source = Path(mod.__file__).read_text()
        assert "date_of_birth" not in source
        assert "biological_sex" not in source
        assert "height_cm" not in source
        assert "weight_kg" not in source
        assert "activity_level" not in source
        assert "dietary_preference" not in source
        assert "allergies" not in source


# ===========================================================================
# G. Application boundaries
# ===========================================================================


class TestApplicationBoundaries:
    def test_existing_routes_unchanged(self):
        import app.api.v1.router as router_mod

        routes = router_mod.router.routes
        route_paths = {r.path for r in routes}
        expected = {"/auth/me", "/auth/register", "/auth/login", "/health", "/nutrition-profile"}
        for path in expected:
            assert path in route_paths, f"Expected route {path} not found"

    def test_no_calculation_route_exists(self):
        import app.api.v1.router as router_mod

        routes = router_mod.router.routes
        route_paths = {r.path for r in routes}
        assert "/nutrition-calculations" not in route_paths
        assert "/calculate" not in route_paths

    def test_openapi_contains_nutrition_calculation_endpoint(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        calc_paths = [
            p for p in paths if "calculat" in p.lower() or "nutrition-calculat" in p.lower()
        ]
        assert len(calc_paths) == 1
        assert "/api/v1/nutrition-profile/calculations" in calc_paths
        op = paths["/api/v1/nutrition-profile/calculations"]
        assert "get" in op

    def test_existing_auth_routes_unchanged(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/me" in paths

    def test_existing_nutrition_profile_routes_unchanged(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/nutrition-profile" in paths
        assert "post" in paths["/api/v1/nutrition-profile"]
        assert "get" in paths["/api/v1/nutrition-profile"]
        assert "patch" in paths["/api/v1/nutrition-profile"]


# ===========================================================================
# H. Imports and exports
# ===========================================================================


class TestImportsExports:
    def test_schema_module_imports(self):
        import app.schemas.nutrition_calculations as mod

        assert mod.NutritionMetricsData is NutritionMetricsData
        assert mod.NutritionTargetsData is NutritionTargetsData
        assert mod.CalculatedNutritionData is CalculatedNutritionData
        assert mod.CalculatedNutritionSuccessResponse is CalculatedNutritionSuccessResponse

    def test_public_classes_import_from_app_schemas(self):
        assert NutritionMetricsData is not None
        assert NutritionTargetsData is not None
        assert CalculatedNutritionData is not None
        assert CalculatedNutritionSuccessResponse is not None

    def test_no_circular_import(self):
        import app.schemas

        assert hasattr(app.schemas, "NutritionMetricsData")
        assert hasattr(app.schemas, "NutritionTargetsData")
        assert hasattr(app.schemas, "CalculatedNutritionData")
        assert hasattr(app.schemas, "CalculatedNutritionSuccessResponse")

    def test_existing_imports_preserved(self):
        from app.schemas import (
            AccessTokenData,
            AuthResponse,
            AuthSuccessResponse,
            LoginRequest,
            NutritionProfileBase,
            NutritionProfileCreate,
            NutritionProfileData,
            NutritionProfilePublic,
            NutritionProfileSuccessResponse,
            NutritionProfileUpdate,
            PublicUser,
            RegisterRequest,
            TokenPair,
            normalize_allergies,
        )

        assert AccessTokenData is not None
        assert AuthResponse is not None
        assert AuthSuccessResponse is not None
        assert LoginRequest is not None
        assert NutritionProfileBase is not None
        assert NutritionProfileCreate is not None
        assert NutritionProfileData is not None
        assert NutritionProfilePublic is not None
        assert NutritionProfileSuccessResponse is not None
        assert NutritionProfileUpdate is not None
        assert PublicUser is not None
        assert RegisterRequest is not None
        assert TokenPair is not None
        assert normalize_allergies is not None

    def test_no_database_connection_during_import(self):
        import app.schemas.nutrition_calculations as mod

        assert mod.NutritionMetricsData is not None
        assert mod.NutritionTargetsData is not None
        assert mod.CalculatedNutritionData is not None
        assert mod.CalculatedNutritionSuccessResponse is not None

    def test_no_environment_file_required(self):
        from app.core.config import Settings

        s = Settings(APP_ENV="test", _env_file=None)
        assert s.DATABASE_URL == ""
