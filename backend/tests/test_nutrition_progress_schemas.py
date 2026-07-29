from __future__ import annotations

import importlib
import inspect
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from app.core.nutrition_calculations import NutritionTargetResult
from app.core.nutrition_logs import DailyNutritionTotals
from app.core.nutrition_progress import (
    DailyNutritionProgress,
    NutrientProgress,
    NutritionProgressStatus,
    calculate_daily_nutrition_progress,
)
from app.schemas.nutrition_progress import (
    DailyNutritionProgressData,
    DailyNutritionProgressSuccessResponse,
    NutrientProgressData,
)

SCHEMA_MODULE = "app.schemas.nutrition_progress"
DOMAIN_MODULE = "app.core.nutrition_progress"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _below_target_nutrient() -> NutrientProgress:
    return NutrientProgress(
        consumed=_dec("1500"),
        target=_dec("2000"),
        remaining=_dec("500"),
        percentage=_dec("75.00"),
        status=NutritionProgressStatus.BELOW_TARGET,
    )


def _target_met_nutrient() -> NutrientProgress:
    return NutrientProgress(
        consumed=_dec("2000"),
        target=_dec("2000"),
        remaining=_dec("0"),
        percentage=_dec("100.00"),
        status=NutritionProgressStatus.TARGET_MET,
    )


def _above_target_nutrient() -> NutrientProgress:
    return NutrientProgress(
        consumed=_dec("2500"),
        target=_dec("2000"),
        remaining=_dec("-500"),
        percentage=_dec("125.00"),
        status=NutritionProgressStatus.ABOVE_TARGET,
    )


def _valid_nutrient_data_dict(
    overrides: dict | None = None,
) -> dict:
    d = {
        "consumed": "1500",
        "target": "2000",
        "remaining": "500",
        "percentage": "75.00",
        "status": "below_target",
    }
    if overrides:
        d.update(overrides)
    return d


def _valid_daily_progress() -> DailyNutritionProgress:
    return DailyNutritionProgress(
        calories=_below_target_nutrient(),
        protein=_target_met_nutrient(),
        carbohydrate=_above_target_nutrient(),
        fat=NutrientProgress(
            consumed=_dec("50"),
            target=_dec("65"),
            remaining=_dec("15"),
            percentage=_dec("76.92"),
            status=NutritionProgressStatus.BELOW_TARGET,
        ),
    )


def _valid_daily_dict(overrides: dict | None = None) -> dict:
    d = {
        "calories": _valid_nutrient_data_dict(
            {
                "consumed": "1500",
                "remaining": "500",
                "percentage": "75.00",
                "status": "below_target",
            }
        ),
        "protein": _valid_nutrient_data_dict(
            {"consumed": "2000", "remaining": "0", "percentage": "100.00", "status": "target_met"}
        ),
        "carbohydrate": _valid_nutrient_data_dict(
            {
                "consumed": "2500",
                "remaining": "-500",
                "percentage": "125.00",
                "status": "above_target",
            }
        ),
        "fat": _valid_nutrient_data_dict(
            {
                "consumed": "50",
                "target": "65",
                "remaining": "15",
                "percentage": "76.92",
                "status": "below_target",
            }
        ),
    }
    if overrides:
        d.update(overrides)
    return d


def _totals(
    *,
    calories: str = "1500",
    protein: str = "80",
    carbohydrate: str = "180",
    fat: str = "50",
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
    protein: str = "2000",
    carbohydrate: str = "2000",
    fat: str = "65",
) -> NutritionTargetResult:
    return NutritionTargetResult(
        calorie_target_kcal_per_day=_dec(calories),
        protein_g_per_day=_dec(protein),
        carbohydrate_g_per_day=_dec(carbohydrate),
        fat_g_per_day=_dec(fat),
    )


def _schema_source() -> str:
    return inspect.getsource(importlib.import_module(SCHEMA_MODULE))


def _domain_source() -> str:
    return inspect.getsource(importlib.import_module(DOMAIN_MODULE))


# ===========================================================================
# A–C. Public module import and exports
# ===========================================================================


class TestModuleImportsAndExports:
    def test_module_imports(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        assert mod is not None

    def test_public_schema_package_exports(self):
        import app.schemas as schemas

        assert hasattr(schemas, "NutrientProgressData")
        assert hasattr(schemas, "DailyNutritionProgressData")
        assert hasattr(schemas, "DailyNutritionProgressSuccessResponse")

    def test_exact_exported_names(self):
        import app.schemas as schemas

        assert "NutrientProgressData" in schemas.__all__
        assert "DailyNutritionProgressData" in schemas.__all__
        assert "DailyNutritionProgressSuccessResponse" in schemas.__all__


# ===========================================================================
# D–H. NutrientProgressData configuration
# ===========================================================================


class TestNutrientProgressDataConfiguration:
    def test_inherits_basemodel(self):
        assert issubclass(NutrientProgressData, BaseModel)

    def test_exact_fields(self):
        fields = set(NutrientProgressData.model_fields)
        expected = {"consumed", "target", "remaining", "percentage", "status"}
        assert fields == expected

    def test_exact_field_annotations(self):
        assert NutrientProgressData.model_fields["consumed"].annotation == Decimal
        assert NutrientProgressData.model_fields["target"].annotation == Decimal
        assert NutrientProgressData.model_fields["remaining"].annotation == Decimal
        assert NutrientProgressData.model_fields["percentage"].annotation == Decimal
        assert NutrientProgressData.model_fields["status"].annotation == NutritionProgressStatus

    def test_extra_forbid(self):
        assert NutrientProgressData.model_config.get("extra") == "forbid"

    def test_frozen(self):
        assert NutrientProgressData.model_config.get("frozen") is True


# ===========================================================================
# I–L. Valid data acceptance
# ===========================================================================


class TestNutrientProgressDataValid:
    def test_valid_below_target(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        assert nd.consumed == _dec("1500")
        assert nd.target == _dec("2000")
        assert nd.remaining == _dec("500")
        assert nd.percentage == _dec("75.00")
        assert nd.status is NutritionProgressStatus.BELOW_TARGET

    def test_valid_exact_target(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {
                    "consumed": "2000",
                    "remaining": "0",
                    "percentage": "100.00",
                    "status": "target_met",
                }
            )
        )
        assert nd.consumed == _dec("2000")
        assert nd.remaining == _dec("0")
        assert nd.percentage == _dec("100.00")
        assert nd.status is NutritionProgressStatus.TARGET_MET

    def test_valid_above_target(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {
                    "consumed": "2500",
                    "remaining": "-500",
                    "percentage": "125.00",
                    "status": "above_target",
                }
            )
        )
        assert nd.consumed == _dec("2500")
        assert nd.remaining == _dec("-500")
        assert nd.percentage == _dec("125.00")
        assert nd.status is NutritionProgressStatus.ABOVE_TARGET

    def test_zero_consumed_accepted(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict({"consumed": "0", "remaining": "2000", "percentage": "0.00"})
        )
        assert nd.consumed == _dec("0")


# ===========================================================================
# M–O. Remaining value acceptance
# ===========================================================================


class TestRemainingValues:
    def test_positive_remaining_accepted(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict({"remaining": "500"}))
        assert nd.remaining == _dec("500")

    def test_zero_remaining_accepted(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict({"remaining": "0"}))
        assert nd.remaining == _dec("0")

    def test_negative_remaining_accepted(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict({"remaining": "-200"}))
        assert nd.remaining == _dec("-200")


# ===========================================================================
# P–S. Percentage acceptance
# ===========================================================================


class TestPercentageAcceptance:
    def test_percentage_below_100_accepted(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {"percentage": "50.00", "consumed": "1000", "remaining": "1000"}
            )
        )
        assert nd.percentage == _dec("50.00")

    def test_percentage_exactly_100_accepted(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {"percentage": "100.00", "consumed": "2000", "remaining": "0"}
            )
        )
        assert nd.percentage == _dec("100.00")

    def test_percentage_above_100_accepted(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {"percentage": "150.00", "consumed": "3000", "remaining": "-1000"}
            )
        )
        assert nd.percentage == _dec("150.00")

    def test_percentage_not_capped(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {"percentage": "999.99", "consumed": "19999.80", "remaining": "-17999.80"}
            )
        )
        assert nd.percentage == _dec("999.99")


# ===========================================================================
# T–W. Status validation
# ===========================================================================


class TestStatusValidation:
    def test_existing_nutrition_progress_status_reused(self):
        assert NutrientProgressData.model_fields["status"].annotation is NutritionProgressStatus

    def test_exact_status_values_accepted(self):
        for status in NutritionProgressStatus:
            nd = NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"status": status.value})
            )
            assert nd.status is status

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"status": "invalid_status"})
            )

    def test_lowercase_enum_json_serialization(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict({"status": "below_target"})
        )
        dumped = nd.model_dump(mode="json")
        assert dumped["status"] == "below_target"


# ===========================================================================
# X–AF. Consumed validation
# ===========================================================================


class TestConsumedValidation:
    def test_nan_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"consumed": Decimal("NaN")})
            )

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"consumed": Decimal("Inf")})
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"consumed": Decimal("-Inf")})
            )

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(_valid_nutrient_data_dict({"consumed": "-1"}))


# ===========================================================================
# AB–AF. Target validation
# ===========================================================================


class TestTargetValidation:
    def test_zero_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(_valid_nutrient_data_dict({"target": "0"}))

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(_valid_nutrient_data_dict({"target": "-100"}))

    def test_nan_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"target": Decimal("NaN")})
            )

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"target": Decimal("Inf")})
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"target": Decimal("-Inf")})
            )


# ===========================================================================
# AG–AI. Remaining validation
# ===========================================================================


class TestRemainingValidation:
    def test_nan_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"remaining": Decimal("NaN")})
            )

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"remaining": Decimal("Inf")})
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"remaining": Decimal("-Inf")})
            )


# ===========================================================================
# AJ–AM. Percentage validation
# ===========================================================================


class TestPercentageValidation:
    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(_valid_nutrient_data_dict({"percentage": "-1"}))

    def test_nan_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"percentage": Decimal("NaN")})
            )

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"percentage": Decimal("Inf")})
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(
                _valid_nutrient_data_dict({"percentage": Decimal("-Inf")})
            )


# ===========================================================================
# AN–AQ. Bool, string, float, None behavior
# ===========================================================================


class TestTypeValidation:
    def test_bool_rejected_for_all_decimal_fields(self):
        for field in ("consumed", "target", "remaining", "percentage"):
            d = _valid_nutrient_data_dict({field: True})
            with pytest.raises(ValidationError):
                NutrientProgressData.model_validate(d)

    def test_string_accepted_for_decimal_fields(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        assert isinstance(nd.consumed, Decimal)
        assert isinstance(nd.target, Decimal)
        assert isinstance(nd.remaining, Decimal)
        assert isinstance(nd.percentage, Decimal)

    def test_float_accepted_for_decimal_fields(self):
        d = _valid_nutrient_data_dict(
            {
                "consumed": 1500.0,
                "target": 2000.0,
                "remaining": 500.0,
                "percentage": 75.0,
            }
        )
        nd = NutrientProgressData.model_validate(d)
        assert isinstance(nd.consumed, Decimal)

    def test_none_rejected_for_every_required_field(self):
        for field in ("consumed", "target", "remaining", "percentage", "status"):
            d = _valid_nutrient_data_dict({field: None})
            with pytest.raises(ValidationError):
                NutrientProgressData.model_validate(d)


# ===========================================================================
# AR–AT. Required/extra/mutation
# ===========================================================================


class TestStructureValidation:
    def test_missing_fields_rejected(self):
        for field in ("consumed", "target", "remaining", "percentage", "status"):
            d = _valid_nutrient_data_dict()
            del d[field]
            with pytest.raises(ValidationError):
                NutrientProgressData.model_validate(d)

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            NutrientProgressData.model_validate(_valid_nutrient_data_dict({"extra_field": "value"}))

    def test_mutation_rejected(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        with pytest.raises(ValidationError):
            nd.consumed = _dec("2000")


# ===========================================================================
# AU–BE. from_result() for NutrientProgressData
# ===========================================================================


class TestNutrientProgressDataFromResult:
    def test_accepts_nutrient_progress(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert isinstance(nd, NutrientProgressData)

    def test_copies_consumed_exactly(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.consumed == result.consumed

    def test_copies_target_exactly(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.target == result.target

    def test_copies_remaining_exactly(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.remaining == result.remaining

    def test_copies_percentage_exactly(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.percentage == result.percentage

    def test_copies_status_exactly(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.status is result.status

    def test_performs_no_recalculation(self):
        result = _below_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.remaining == _dec("500")
        assert nd.percentage == _dec("75.00")
        assert nd.status is NutritionProgressStatus.BELOW_TARGET

    def test_performs_no_rounding(self):
        result = NutrientProgress(
            consumed=_dec("1333.333"),
            target=_dec("2000"),
            remaining=_dec("666.667"),
            percentage=_dec("66.67"),
            status=NutritionProgressStatus.BELOW_TARGET,
        )
        nd = NutrientProgressData.from_result(result)
        assert nd.percentage == _dec("66.67")

    def test_performs_no_status_reclassification(self):
        result = _above_target_nutrient()
        nd = NutrientProgressData.from_result(result)
        assert nd.status is NutritionProgressStatus.ABOVE_TARGET

    def test_does_not_mutate_input(self):
        result = _below_target_nutrient()
        consumed_before = result.consumed
        NutrientProgressData.from_result(result)
        assert result.consumed == consumed_before

    def test_deterministic(self):
        result = _below_target_nutrient()
        nd1 = NutrientProgressData.from_result(result)
        nd2 = NutrientProgressData.from_result(result)
        assert nd1.model_dump() == nd2.model_dump()


# ===========================================================================
# BF–BQ. DailyNutritionProgressData configuration
# ===========================================================================


class TestDailyNutritionProgressDataConfiguration:
    def test_inherits_basemodel(self):
        assert issubclass(DailyNutritionProgressData, BaseModel)

    def test_exact_fields(self):
        fields = set(DailyNutritionProgressData.model_fields)
        expected = {"calories", "protein", "carbohydrate", "fat", "requires_onboarding"}
        assert fields == expected

    def test_exact_nested_types(self):
        assert (
            DailyNutritionProgressData.model_fields["calories"].annotation == NutrientProgressData
        )
        assert DailyNutritionProgressData.model_fields["protein"].annotation == NutrientProgressData
        assert (
            DailyNutritionProgressData.model_fields["carbohydrate"].annotation
            == NutrientProgressData
        )
        assert DailyNutritionProgressData.model_fields["fat"].annotation == NutrientProgressData

    def test_all_four_sections_required(self):
        for field in ("calories", "protein", "carbohydrate", "fat"):
            assert DailyNutritionProgressData.model_fields[field].is_required()

    def test_extra_top_level_field_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionProgressData.model_validate(_valid_daily_dict({"extra_field": "value"}))

    def test_extra_nested_field_rejected(self):
        d = _valid_daily_dict()
        d["calories"]["extra"] = "value"
        with pytest.raises(ValidationError):
            DailyNutritionProgressData.model_validate(d)

    def test_top_level_mutation_rejected(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        with pytest.raises(ValidationError):
            dp.calories = NutrientProgressData.model_validate(_valid_nutrient_data_dict())

    def test_nested_mutation_rejected(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        with pytest.raises(ValidationError):
            dp.calories.consumed = _dec("9999")


# ===========================================================================
# BJ–BN. Missing/null nested sections
# ===========================================================================


class TestDailyNutritionProgressMissing:
    def test_missing_calories_rejected(self):
        d = _valid_daily_dict()
        del d["calories"]
        with pytest.raises(ValidationError):
            DailyNutritionProgressData.model_validate(d)

    def test_missing_protein_rejected(self):
        d = _valid_daily_dict()
        del d["protein"]
        with pytest.raises(ValidationError):
            DailyNutritionProgressData.model_validate(d)

    def test_missing_carbohydrate_rejected(self):
        d = _valid_daily_dict()
        del d["carbohydrate"]
        with pytest.raises(ValidationError):
            DailyNutritionProgressData.model_validate(d)

    def test_missing_fat_rejected(self):
        d = _valid_daily_dict()
        del d["fat"]
        with pytest.raises(ValidationError):
            DailyNutritionProgressData.model_validate(d)

    def test_null_nested_section_rejected(self):
        for field in ("calories", "protein", "carbohydrate", "fat"):
            d = _valid_daily_dict({field: None})
            with pytest.raises(ValidationError):
                DailyNutritionProgressData.model_validate(d)


# ===========================================================================
# BS–CA. DailyNutritionProgressData.from_result()
# ===========================================================================


class TestDailyNutritionProgressDataFromResult:
    def test_accepts_daily_nutrition_progress(self):
        result = _valid_daily_progress()
        dp = DailyNutritionProgressData.from_result(result)
        assert isinstance(dp, DailyNutritionProgressData)

    def test_reuses_nested_conversion_helper(self):
        result = _valid_daily_progress()
        dp = DailyNutritionProgressData.from_result(result)
        assert isinstance(dp.calories, NutrientProgressData)
        assert isinstance(dp.protein, NutrientProgressData)
        assert isinstance(dp.carbohydrate, NutrientProgressData)
        assert isinstance(dp.fat, NutrientProgressData)

    def test_copies_all_four_sections(self):
        result = _valid_daily_progress()
        dp = DailyNutritionProgressData.from_result(result)
        assert dp.calories.consumed == result.calories.consumed
        assert dp.protein.consumed == result.protein.consumed
        assert dp.carbohydrate.consumed == result.carbohydrate.consumed
        assert dp.fat.consumed == result.fat.consumed

    def test_preserves_order(self):
        fields = list(DailyNutritionProgressData.model_fields)
        domain_fields = ["calories", "protein", "carbohydrate", "fat", "requires_onboarding"]
        assert fields == domain_fields

    def test_preserves_negative_remaining(self):
        result = _valid_daily_progress()
        dp = DailyNutritionProgressData.from_result(result)
        assert dp.carbohydrate.remaining == _dec("-500")

    def test_preserves_percentage_above_100(self):
        result = _valid_daily_progress()
        dp = DailyNutritionProgressData.from_result(result)
        assert dp.carbohydrate.percentage == _dec("125.00")

    def test_preserves_statuses(self):
        result = _valid_daily_progress()
        dp = DailyNutritionProgressData.from_result(result)
        assert dp.calories.status is NutritionProgressStatus.BELOW_TARGET
        assert dp.protein.status is NutritionProgressStatus.TARGET_MET
        assert dp.carbohydrate.status is NutritionProgressStatus.ABOVE_TARGET
        assert dp.fat.status is NutritionProgressStatus.BELOW_TARGET

    def test_does_not_mutate_input(self):
        result = _valid_daily_progress()
        calories_before = result.calories.consumed
        DailyNutritionProgressData.from_result(result)
        assert result.calories.consumed == calories_before

    def test_deterministic(self):
        result = _valid_daily_progress()
        dp1 = DailyNutritionProgressData.from_result(result)
        dp2 = DailyNutritionProgressData.from_result(result)
        assert dp1.model_dump() == dp2.model_dump()


# ===========================================================================
# CB–CJ. DailyNutritionProgressSuccessResponse
# ===========================================================================


class TestDailyNutritionProgressSuccessResponse:
    def test_inherits_basemodel(self):
        assert issubclass(DailyNutritionProgressSuccessResponse, BaseModel)

    def test_exact_fields(self):
        fields = set(DailyNutritionProgressSuccessResponse.model_fields)
        expected = {"success", "message", "data"}
        assert fields == expected

    def test_success_defaults_to_true(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        r = DailyNutritionProgressSuccessResponse(data=dp)
        assert r.success is True

    def test_success_false_rejected(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        with pytest.raises(ValidationError):
            DailyNutritionProgressSuccessResponse(data=dp, success=False)

    def test_exact_default_message(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        r = DailyNutritionProgressSuccessResponse(data=dp)
        assert r.message == "Daily nutrition target progress calculated successfully."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            DailyNutritionProgressSuccessResponse()

    def test_data_null_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionProgressSuccessResponse(data=None)

    def test_extra_fields_rejected(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        with pytest.raises(ValidationError):
            DailyNutritionProgressSuccessResponse(
                data=dp,
                extra_field="value",
            )


# ===========================================================================
# CK–CO. Decimal and JSON serialization
# ===========================================================================


class TestDecimalSerialization:
    def test_decimal_values_remain_decimal_in_python(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        assert isinstance(nd.consumed, Decimal)
        assert isinstance(nd.target, Decimal)
        assert isinstance(nd.remaining, Decimal)
        assert isinstance(nd.percentage, Decimal)

    def test_decimal_values_serialize_as_json_strings(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        raw = nd.model_dump_json()
        import json

        obj = json.loads(raw)
        assert obj["consumed"] == "1500"
        assert obj["target"] == "2000"
        assert obj["remaining"] == "500"
        assert obj["percentage"] == "75.00"

    def test_negative_remaining_json_serialization(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {"remaining": "-200.00", "consumed": "2200", "percentage": "110.00"}
            )
        )
        raw = nd.model_dump_json()
        import json

        obj = json.loads(raw)
        assert obj["remaining"] == "-200.00"

    def test_above_100_percentage_json_serialization(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict(
                {"percentage": "125.00", "consumed": "2500", "remaining": "-500"}
            )
        )
        raw = nd.model_dump_json()
        import json

        obj = json.loads(raw)
        assert obj["percentage"] == "125.00"

    def test_enum_json_serialization(self):
        nd = NutrientProgressData.model_validate(
            _valid_nutrient_data_dict({"status": "above_target"})
        )
        raw = nd.model_dump_json()
        import json

        obj = json.loads(raw)
        assert obj["status"] == "above_target"


# ===========================================================================
# CP. Full known domain-to-response conversion
# ===========================================================================


class TestFullDomainToResponse:
    def test_full_conversion(self):
        totals = _totals()
        targets = _targets()
        domain = calculate_daily_nutrition_progress(totals=totals, targets=targets)
        data = DailyNutritionProgressData.from_result(domain)
        response = DailyNutritionProgressSuccessResponse(data=data)
        assert response.success is True
        assert response.message == "Daily nutrition target progress calculated successfully."
        assert response.data.calories.consumed == _dec("1500")
        assert response.data.calories.target == _dec("2000")
        assert response.data.calories.remaining == _dec("500")
        assert response.data.calories.percentage == _dec("75.00")
        assert response.data.calories.status is NutritionProgressStatus.BELOW_TARGET


# ===========================================================================
# CQ–CR. model_dump and model_dump_json
# ===========================================================================


class TestModelDump:
    def test_model_dump(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        dumped = nd.model_dump()
        assert dumped["consumed"] == _dec("1500")
        assert dumped["target"] == _dec("2000")
        assert dumped["remaining"] == _dec("500")
        assert dumped["percentage"] == _dec("75.00")
        assert dumped["status"] == NutritionProgressStatus.BELOW_TARGET

    def test_model_dump_json(self):
        nd = NutrientProgressData.model_validate(_valid_nutrient_data_dict())
        raw = nd.model_dump_json()
        import json

        obj = json.loads(raw)
        assert obj["consumed"] == "1500"
        assert obj["target"] == "2000"
        assert obj["status"] == "below_target"


# ===========================================================================
# CS–CV. No formula duplication
# ===========================================================================


class TestNoFormulaDuplication:
    def test_no_formula_duplication(self):
        src = _schema_source()
        assert "remaining = " not in src
        assert "percentage = " not in src
        assert "status = " not in src

    def test_no_remaining_recalculation(self):
        src = _schema_source()
        assert "target - consumed" not in src
        assert "consumed - target" not in src

    def test_no_percentage_recalculation(self):
        src = _schema_source()
        assert "/ target * 100" not in src
        assert "* Decimal" not in src

    def test_no_status_reclassification(self):
        src = _schema_source()
        assert "consumed < target" not in src
        assert "consumed == target" not in src
        assert "consumed > target" not in src


# ===========================================================================
# CW–DJ. Schema boundaries and purity
# ===========================================================================


class TestSchemaBoundaries:
    def test_no_fastapi_import(self):
        src = _schema_source().lower()
        assert "fastapi" not in src

    def test_no_starlette_import(self):
        src = _schema_source().lower()
        assert "starlette" not in src

    def test_no_sqlalchemy_import(self):
        src = _schema_source().lower()
        assert "sqlalchemy" not in src

    def test_no_database_import(self):
        src = _schema_source().lower()
        assert "session" not in src
        assert "engine" not in src

    def test_no_repository_import(self):
        src = _schema_source().lower()
        assert "repository" not in src

    def test_no_service_import(self):
        src = _schema_source().lower()
        assert "service" not in src

    def test_no_api_router_import(self):
        src = _schema_source().lower()
        assert "router" not in src

    def test_no_environment_access(self):
        src = _schema_source().lower()
        assert "environ" not in src
        assert "os.getenv" not in src

    def test_no_network_access(self):
        src = _schema_source().lower()
        assert "import request" not in src
        assert "urllib" not in src
        assert "httpx" not in src

    def test_no_system_clock(self):
        src = _schema_source()
        assert "date.today" not in src
        assert "datetime.now" not in src
        assert "datetime.utcnow" not in src
        assert "time.time" not in src

    def test_no_random_behavior(self):
        src = _schema_source().lower()
        assert "random" not in src

    def test_no_filesystem_access(self):
        src = _schema_source().lower()
        assert "open(" not in src
        assert "pathlib" not in src
        assert "os.path" not in src

    def test_no_mutable_global_state(self):
        src = _schema_source()
        assert "global " not in src


class TestDomainPydanticFree:
    def test_domain_module_remains_pydantic_free(self):
        src = _domain_source().lower()
        assert "pydantic" not in src
        assert "basemodel" not in src

    def test_domain_module_no_schema_import(self):
        src = _domain_source()
        assert "app.schemas" not in src


# ===========================================================================
# DK–DO. No health/score/recommendation/warning
# ===========================================================================


class TestNoForbiddenFeatures:
    def test_no_health_score(self):
        src = _schema_source().lower()
        assert "health_score" not in src
        assert "health score" not in src

    def test_no_nutrition_score(self):
        src = _schema_source().lower()
        assert "nutrition_score" not in src
        assert "nutrition score" not in src

    def test_no_adherence_score(self):
        src = _schema_source().lower()
        assert "adherence" not in src

    def test_no_recommendation_logic(self):
        src = _schema_source().lower()
        assert "recommend" not in src

    def test_no_warning_generation(self):
        src = _schema_source().lower()
        assert "warning" not in src


# ===========================================================================
# DP. No API endpoint
# ===========================================================================


class TestNoAPIEndpoint:
    def test_no_api_endpoint(self):
        src = _schema_source().lower()
        assert "router" not in src
        assert "endpoint" not in src


# ===========================================================================
# DQ–DS. Existing behavior unchanged
# ===========================================================================


class TestExistingBehaviorUnchanged:
    def test_existing_phase_4f7_domain_unchanged(self):
        import app.core.nutrition_progress as domain

        assert hasattr(domain, "NutritionProgressStatus")
        assert hasattr(domain, "NutrientProgress")
        assert hasattr(domain, "DailyNutritionProgress")
        assert hasattr(domain, "calculate_daily_nutrition_progress")

    def test_existing_calculation_schemas_unchanged(self):
        from app.schemas.nutrition_calculations import (
            CalculatedNutritionData,
            CalculatedNutritionSuccessResponse,
            NutritionMetricsData,
            NutritionTargetsData,
        )

        assert CalculatedNutritionData is not None
        assert CalculatedNutritionSuccessResponse is not None
        assert NutritionMetricsData is not None
        assert NutritionTargetsData is not None

    def test_existing_nutrition_log_schemas_unchanged(self):
        from app.schemas.nutrition_logs import (
            DailyNutritionLogSuccessResponse,
            DailyNutritionLogSummaryData,
            DailyNutritionTotalsData,
            NutritionLogEntryCreate,
            NutritionLogEntryData,
        )

        assert DailyNutritionLogSuccessResponse is not None
        assert DailyNutritionLogSummaryData is not None
        assert DailyNutritionTotalsData is not None
        assert NutritionLogEntryCreate is not None
        assert NutritionLogEntryData is not None


# ===========================================================================
# Custom message test
# ===========================================================================


class TestCustomMessage:
    def test_custom_valid_message(self):
        dp = DailyNutritionProgressData.model_validate(_valid_daily_dict())
        r = DailyNutritionProgressSuccessResponse(
            data=dp,
            message="Custom message.",
        )
        assert r.message == "Custom message."
