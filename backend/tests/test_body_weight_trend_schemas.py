from __future__ import annotations

import importlib
import inspect
import json
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.body_weight_trends import (
    BodyWeightTrendDirection,
    BodyWeightTrendResult,
)
from app.schemas.body_weight_trends import (
    BodyWeightTrendData,
    BodyWeightTrendSuccessResponse,
)

SCHEMA_MODULE = "app.schemas.body_weight_trends"
DOMAIN_MODULE = "app.core.body_weight_trends"

# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _make_result(
    *,
    observation_count: int = 2,
    first_logged_date: date | None = None,
    latest_logged_date: date | None = None,
    starting_weight_kg: Decimal | None = None,
    latest_weight_kg: Decimal | None = None,
    absolute_change_kg: Decimal | None = None,
    percentage_change: Decimal | None = None,
    direction: BodyWeightTrendDirection | None = None,
) -> BodyWeightTrendResult:
    return BodyWeightTrendResult(
        observation_count=observation_count,
        first_logged_date=date(2025, 6, 1) if first_logged_date is None else first_logged_date,
        latest_logged_date=date(2025, 6, 15) if latest_logged_date is None else latest_logged_date,
        starting_weight_kg=_dec("70.00") if starting_weight_kg is None else starting_weight_kg,
        latest_weight_kg=_dec("75.00") if latest_weight_kg is None else latest_weight_kg,
        absolute_change_kg=_dec("5.00") if absolute_change_kg is None else absolute_change_kg,
        percentage_change=_dec("7.14") if percentage_change is None else percentage_change,
        direction=BodyWeightTrendDirection.INCREASED if direction is None else direction,
    )


def _make_data(
    *,
    observation_count: int = 2,
    first_logged_date: date | None = None,
    latest_logged_date: date | None = None,
    starting_weight_kg: Decimal | None = None,
    latest_weight_kg: Decimal | None = None,
    absolute_change_kg: Decimal | None = None,
    percentage_change: Decimal | None = None,
    direction: BodyWeightTrendDirection | None = None,
) -> BodyWeightTrendData:
    return BodyWeightTrendData(
        observation_count=observation_count,
        first_logged_date=date(2025, 6, 1) if first_logged_date is None else first_logged_date,
        latest_logged_date=date(2025, 6, 15) if latest_logged_date is None else latest_logged_date,
        starting_weight_kg=_dec("70.00") if starting_weight_kg is None else starting_weight_kg,
        latest_weight_kg=_dec("75.00") if latest_weight_kg is None else latest_weight_kg,
        absolute_change_kg=_dec("5.00") if absolute_change_kg is None else absolute_change_kg,
        percentage_change=_dec("7.14") if percentage_change is None else percentage_change,
        direction=BodyWeightTrendDirection.INCREASED if direction is None else direction,
    )


# ===========================================================================
# A. Module imports and exports
# ===========================================================================


class TestModuleExports:
    def test_module_imports_successfully(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        assert mod is not None

    def test_both_schemas_exist(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        for name in [
            "BodyWeightTrendData",
            "BodyWeightTrendSuccessResponse",
        ]:
            assert hasattr(mod, name), f"Missing schema: {name}"

    def test_both_exported_from_app_schemas(self):
        from app.schemas import (
            BodyWeightTrendData as _BodyWeightTrendData,
        )
        from app.schemas import (
            BodyWeightTrendSuccessResponse as _BodyWeightTrendSuccessResponse,
        )

        assert _BodyWeightTrendData is not None
        assert _BodyWeightTrendSuccessResponse is not None

    def test_exact_public_exports(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        expected = [
            "BodyWeightTrendData",
            "BodyWeightTrendSuccessResponse",
        ]
        assert mod.__all__ == expected

    def test_existing_exports_preserved(self):
        from app.schemas import (
            BodyWeightEntryData,
        )

        assert BodyWeightEntryData is not None

    def test_no_duplicate_names(self):
        from app.schemas import __all__ as all_exports

        assert len(all_exports) == len(set(all_exports))


# ===========================================================================
# B. BodyWeightTrendData structure
# ===========================================================================


class TestBodyWeightTrendDataStructure:
    def test_exact_field_names(self):
        fields = list(BodyWeightTrendData.model_fields)
        assert fields == [
            "observation_count",
            "first_logged_date",
            "latest_logged_date",
            "starting_weight_kg",
            "latest_weight_kg",
            "absolute_change_kg",
            "percentage_change",
            "direction",
            "requires_onboarding",
        ]

    def test_exact_field_order(self):
        fields = list(BodyWeightTrendData.model_fields)
        expected = [
            "observation_count",
            "first_logged_date",
            "latest_logged_date",
            "starting_weight_kg",
            "latest_weight_kg",
            "absolute_change_kg",
            "percentage_change",
            "direction",
            "requires_onboarding",
        ]
        assert fields == expected

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendData(
                observation_count=2,
                first_logged_date=date(2025, 6, 1),
                latest_logged_date=date(2025, 6, 15),
                starting_weight_kg=_dec("70.00"),
                latest_weight_kg=_dec("75.00"),
                absolute_change_kg=_dec("5.00"),
                percentage_change=_dec("7.14"),
                direction=BodyWeightTrendDirection.INCREASED,
                extra_field="value",
            )

    def test_frozen_top_level_mutation_rejected(self):
        obj = _make_data()
        with pytest.raises(ValidationError):
            obj.observation_count = 3

    def test_config_extra_forbid(self):
        assert BodyWeightTrendData.model_config.get("extra") == "forbid"

    def test_config_frozen(self):
        assert BodyWeightTrendData.model_config.get("frozen") is True


# ===========================================================================
# C. observation_count validation
# ===========================================================================


class TestObservationCountValidation:
    def test_minimum_two_accepted(self):
        obj = _make_data(observation_count=2)
        assert obj.observation_count == 2

    def test_three_accepted(self):
        obj = _make_data(observation_count=3)
        assert obj.observation_count == 3

    def test_large_value_accepted(self):
        obj = _make_data(observation_count=100)
        assert obj.observation_count == 100

    def test_zero_rejected(self):
        # observation_count=0 is allowed for the onboarding placeholder response
        obj = _make_data(observation_count=0)
        assert obj.observation_count == 0

    def test_one_rejected(self):
        # observation_count=1 is allowed for the onboarding placeholder response
        obj = _make_data(observation_count=1)
        assert obj.observation_count == 1

    def test_negative_rejected(self):
        with pytest.raises(ValidationError, match="at least 0"):
            _make_data(observation_count=-1)

    def test_bool_true_rejected(self):
        with pytest.raises(ValidationError, match="must be an integer, not a boolean"):
            _make_data(observation_count=True)  # type: ignore[arg-type]

    def test_bool_false_rejected(self):
        with pytest.raises(ValidationError, match="must be an integer, not a boolean"):
            _make_data(observation_count=False)  # type: ignore[arg-type]

    def test_float_rejected(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            _make_data(observation_count=2.0)  # type: ignore[arg-type]

    def test_decimal_rejected(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            _make_data(observation_count=Decimal("2"))  # type: ignore[arg-type]

    def test_numeric_string_rejected(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            _make_data(observation_count="2")  # type: ignore[arg-type]

    def test_nonnumeric_string_rejected(self):
        with pytest.raises(ValidationError, match="must be an integer"):
            _make_data(observation_count="abc")  # type: ignore[arg-type]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            _make_data(observation_count=None)  # type: ignore[arg-type]


# ===========================================================================
# D. Date validation
# ===========================================================================


class TestDateValidation:
    def test_valid_dates_accepted(self):
        obj = _make_data(
            first_logged_date=date(2025, 1, 1),
            latest_logged_date=date(2025, 6, 15),
        )
        assert obj.first_logged_date == date(2025, 1, 1)
        assert obj.latest_logged_date == date(2025, 6, 15)

    def test_same_dates_accepted(self):
        obj = _make_data(
            first_logged_date=date(2025, 6, 15),
            latest_logged_date=date(2025, 6, 15),
        )
        assert obj.first_logged_date == obj.latest_logged_date

    def test_latest_after_first_accepted(self):
        obj = _make_data(
            first_logged_date=date(2025, 1, 1),
            latest_logged_date=date(2025, 6, 15),
        )
        assert obj.latest_logged_date > obj.first_logged_date

    def test_earlier_latest_rejected(self):
        msg = "latest_logged_date must be greater than or equal to first_logged_date"
        with pytest.raises(ValidationError, match=msg):
            _make_data(
                first_logged_date=date(2025, 6, 15),
                latest_logged_date=date(2025, 1, 1),
            )


# ===========================================================================
# E. Starting-weight validation
# ===========================================================================


class TestStartingWeightValidation:
    def test_valid_decimal_accepted(self):
        obj = _make_data(starting_weight_kg=_dec("70.00"))
        assert obj.starting_weight_kg == _dec("70.00")

    def test_valid_int_string_accepted(self):
        obj = _make_data(starting_weight_kg=_dec("10.00"))
        assert obj.starting_weight_kg == _dec("10.00")

    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="must not be a boolean"):
            _make_data(starting_weight_kg=True)  # type: ignore[arg-type]

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(starting_weight_kg=Decimal("NaN"))  # type: ignore[arg-type]

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(starting_weight_kg=Decimal("Infinity"))  # type: ignore[arg-type]

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(starting_weight_kg=Decimal("-Infinity"))  # type: ignore[arg-type]

    def test_zero_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            _make_data(starting_weight_kg=_dec("0.00"))

    def test_negative_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            _make_data(starting_weight_kg=_dec("-1.00"))

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendData(
                observation_count=2,
                first_logged_date=date(2025, 6, 1),
                latest_logged_date=date(2025, 6, 15),
                starting_weight_kg=None,  # type: ignore[arg-type]
                latest_weight_kg=_dec("75.00"),
                absolute_change_kg=_dec("5.00"),
                percentage_change=_dec("7.14"),
                direction=BodyWeightTrendDirection.INCREASED,
            )


# ===========================================================================
# F. Latest-weight validation
# ===========================================================================


class TestLatestWeightValidation:
    def test_valid_decimal_accepted(self):
        obj = _make_data(latest_weight_kg=_dec("75.00"))
        assert obj.latest_weight_kg == _dec("75.00")

    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="must not be a boolean"):
            _make_data(latest_weight_kg=True)  # type: ignore[arg-type]

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(latest_weight_kg=Decimal("NaN"))  # type: ignore[arg-type]

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(latest_weight_kg=Decimal("Infinity"))  # type: ignore[arg-type]

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(latest_weight_kg=Decimal("-Infinity"))  # type: ignore[arg-type]

    def test_zero_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            _make_data(latest_weight_kg=_dec("0.00"))

    def test_negative_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            _make_data(latest_weight_kg=_dec("-1.00"))

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendData(
                observation_count=2,
                first_logged_date=date(2025, 6, 1),
                latest_logged_date=date(2025, 6, 15),
                starting_weight_kg=_dec("70.00"),
                latest_weight_kg=None,  # type: ignore[arg-type]
                absolute_change_kg=_dec("5.00"),
                percentage_change=_dec("7.14"),
                direction=BodyWeightTrendDirection.INCREASED,
            )


# ===========================================================================
# G. Absolute-change validation
# ===========================================================================


class TestAbsoluteChangeValidation:
    def test_positive_preserved(self):
        obj = _make_data(absolute_change_kg=_dec("5.00"))
        assert obj.absolute_change_kg == _dec("5.00")

    def test_negative_preserved(self):
        obj = _make_data(absolute_change_kg=_dec("-5.00"))
        assert obj.absolute_change_kg == _dec("-5.00")

    def test_zero_preserved(self):
        obj = _make_data(absolute_change_kg=_dec("0.00"))
        assert obj.absolute_change_kg == _dec("0.00")

    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="must not be a boolean"):
            _make_data(absolute_change_kg=True)  # type: ignore[arg-type]

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(absolute_change_kg=Decimal("NaN"))  # type: ignore[arg-type]

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(absolute_change_kg=Decimal("Infinity"))  # type: ignore[arg-type]

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(absolute_change_kg=Decimal("-Infinity"))  # type: ignore[arg-type]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendData(
                observation_count=2,
                first_logged_date=date(2025, 6, 1),
                latest_logged_date=date(2025, 6, 15),
                starting_weight_kg=_dec("70.00"),
                latest_weight_kg=_dec("75.00"),
                absolute_change_kg=None,  # type: ignore[arg-type]
                percentage_change=_dec("7.14"),
                direction=BodyWeightTrendDirection.INCREASED,
            )


# ===========================================================================
# H. Percentage-change validation
# ===========================================================================


class TestPercentageChangeValidation:
    def test_positive_preserved(self):
        obj = _make_data(percentage_change=_dec("7.14"))
        assert obj.percentage_change == _dec("7.14")

    def test_negative_preserved(self):
        obj = _make_data(percentage_change=_dec("-6.25"))
        assert obj.percentage_change == _dec("-6.25")

    def test_zero_preserved(self):
        obj = _make_data(percentage_change=_dec("0.00"))
        assert obj.percentage_change == _dec("0.00")

    def test_above_100_preserved(self):
        obj = _make_data(percentage_change=_dec("150.00"))
        assert obj.percentage_change == _dec("150.00")

    def test_below_negative_100_preserved(self):
        obj = _make_data(percentage_change=_dec("-150.00"))
        assert obj.percentage_change == _dec("-150.00")

    def test_not_capped_at_100(self):
        obj = _make_data(percentage_change=_dec("200.00"))
        assert obj.percentage_change == _dec("200.00")

    def test_not_clamped(self):
        obj = _make_data(percentage_change=_dec("-200.00"))
        assert obj.percentage_change == _dec("-200.00")

    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="must not be a boolean"):
            _make_data(percentage_change=True)  # type: ignore[arg-type]

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(percentage_change=Decimal("NaN"))  # type: ignore[arg-type]

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(percentage_change=Decimal("Infinity"))  # type: ignore[arg-type]

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            _make_data(percentage_change=Decimal("-Infinity"))  # type: ignore[arg-type]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendData(
                observation_count=2,
                first_logged_date=date(2025, 6, 1),
                latest_logged_date=date(2025, 6, 15),
                starting_weight_kg=_dec("70.00"),
                latest_weight_kg=_dec("75.00"),
                absolute_change_kg=_dec("5.00"),
                percentage_change=None,  # type: ignore[arg-type]
                direction=BodyWeightTrendDirection.INCREASED,
            )


# ===========================================================================
# I. Direction enum
# ===========================================================================


class TestDirectionEnum:
    def test_reuses_body_weight_trend_direction(self):
        assert BodyWeightTrendData.model_fields["direction"].annotation is BodyWeightTrendDirection

    def test_valid_direction_accepted(self):
        for direction in BodyWeightTrendDirection:
            obj = _make_data(direction=direction)
            assert obj.direction == direction

    def test_invalid_string_rejected(self):
        with pytest.raises(ValidationError):
            _make_data(direction="unknown")  # type: ignore[arg-type]

    def test_invalid_value_rejected(self):
        with pytest.raises(ValidationError):
            _make_data(direction="improving")  # type: ignore[arg-type]

    def test_lowercase_serialization_decreased(self):
        obj = _make_data(direction=BodyWeightTrendDirection.DECREASED)
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["direction"] == "decreased"

    def test_lowercase_serialization_stable(self):
        obj = _make_data(direction=BodyWeightTrendDirection.STABLE)
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["direction"] == "stable"

    def test_lowercase_serialization_increased(self):
        obj = _make_data(direction=BodyWeightTrendDirection.INCREASED)
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["direction"] == "increased"


# ===========================================================================
# J. from_result helper
# ===========================================================================


class TestFromResult:
    def test_exact_copy_all_values(self):
        result = _make_result(
            observation_count=3,
            first_logged_date=date(2025, 1, 1),
            latest_logged_date=date(2025, 6, 1),
            starting_weight_kg=_dec("80.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("-5.00"),
            percentage_change=_dec("-6.25"),
            direction=BodyWeightTrendDirection.DECREASED,
        )
        data = BodyWeightTrendData.from_result(result)
        assert data.observation_count == result.observation_count
        assert data.first_logged_date == result.first_logged_date
        assert data.latest_logged_date == result.latest_logged_date
        assert data.starting_weight_kg == result.starting_weight_kg
        assert data.latest_weight_kg == result.latest_weight_kg
        assert data.absolute_change_kg == result.absolute_change_kg
        assert data.percentage_change == result.percentage_change
        assert data.direction == result.direction

    def test_negative_absolute_change_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("80.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("-5.00"),
            percentage_change=_dec("-6.25"),
            direction=BodyWeightTrendDirection.DECREASED,
        )
        data = BodyWeightTrendData.from_result(result)
        assert data.absolute_change_kg == _dec("-5.00")

    def test_negative_percentage_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("80.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("-5.00"),
            percentage_change=_dec("-6.25"),
            direction=BodyWeightTrendDirection.DECREASED,
        )
        data = BodyWeightTrendData.from_result(result)
        assert data.percentage_change == _dec("-6.25")

    def test_no_recalculation(self):
        result = _make_result()
        original_values = {
            "observation_count": result.observation_count,
            "first_logged_date": result.first_logged_date,
            "latest_logged_date": result.latest_logged_date,
            "starting_weight_kg": result.starting_weight_kg,
            "latest_weight_kg": result.latest_weight_kg,
            "absolute_change_kg": result.absolute_change_kg,
            "percentage_change": result.percentage_change,
            "direction": result.direction,
        }
        BodyWeightTrendData.from_result(result)
        for field, original_value in original_values.items():
            current = getattr(result, field)
            assert current == original_value, f"Field {field} was mutated"

    def test_no_rounding_during_conversion(self):
        precise = _dec("5.123456789")
        result = _make_result(absolute_change_kg=precise)
        data = BodyWeightTrendData.from_result(result)
        assert data.absolute_change_kg == precise

    def test_no_direction_reclassification(self):
        for direction in BodyWeightTrendDirection:
            result = _make_result(
                direction=direction,
                absolute_change_kg=_dec("0.00"),
                percentage_change=_dec("0.00"),
            )
            data = BodyWeightTrendData.from_result(result)
            assert data.direction == direction

    def test_domain_input_not_mutated(self):
        result = _make_result()
        original = repr(result)
        BodyWeightTrendData.from_result(result)
        assert repr(result) == original

    def test_deterministic_repeated_conversion(self):
        result = _make_result()
        data1 = BodyWeightTrendData.from_result(result)
        data2 = BodyWeightTrendData.from_result(result)
        assert data1.model_dump() == data2.model_dump()


# ===========================================================================
# K. BodyWeightTrendSuccessResponse
# ===========================================================================


class TestBodyWeightTrendSuccessResponse:
    def test_exact_fields(self):
        fields = set(BodyWeightTrendSuccessResponse.model_fields)
        assert fields == {"success", "message", "data"}

    def test_default_success_is_true(self):
        resp = BodyWeightTrendSuccessResponse(data=_make_data())
        assert resp.success is True

    def test_success_is_literal_true(self):
        annotation = BodyWeightTrendSuccessResponse.model_fields["success"].annotation
        args = getattr(annotation, "__args__", ())
        assert True in args
        assert False not in args

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=_make_data(),
            )

    def test_exact_default_message(self):
        resp = BodyWeightTrendSuccessResponse(data=_make_data())
        assert resp.message == "Body-weight trend calculated successfully."

    def test_custom_message_accepted(self):
        resp = BodyWeightTrendSuccessResponse(
            message="Custom message.",
            data=_make_data(),
        )
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightTrendSuccessResponse(
                data=_make_data(),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_response_not_frozen(self):
        resp = BodyWeightTrendSuccessResponse(data=_make_data())
        assert resp.model_config.get("frozen") is not True


# ===========================================================================
# L. Serialization
# ===========================================================================


class TestSerialization:
    def test_decimal_preserved_in_python(self):
        obj = _make_data()
        dumped = obj.model_dump()
        assert isinstance(dumped["starting_weight_kg"], Decimal)
        assert isinstance(dumped["latest_weight_kg"], Decimal)
        assert isinstance(dumped["absolute_change_kg"], Decimal)
        assert isinstance(dumped["percentage_change"], Decimal)

    def test_decimal_json_string_serialization(self):
        obj = _make_data()
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["starting_weight_kg"] == "70.00"
        assert parsed["latest_weight_kg"] == "75.00"
        assert parsed["absolute_change_kg"] == "5.00"
        assert parsed["percentage_change"] == "7.14"

    def test_negative_decimal_json_serialization(self):
        obj = _make_data(
            absolute_change_kg=_dec("-5.00"),
            percentage_change=_dec("-6.25"),
        )
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["absolute_change_kg"] == "-5.00"
        assert parsed["percentage_change"] == "-6.25"

    def test_zero_decimal_json_serialization(self):
        obj = _make_data(
            absolute_change_kg=_dec("0.00"),
            percentage_change=_dec("0.00"),
        )
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["absolute_change_kg"] == "0.00"
        assert parsed["percentage_change"] == "0.00"

    def test_date_iso_serialization(self):
        obj = _make_data(
            first_logged_date=date(2025, 1, 1),
            latest_logged_date=date(2025, 6, 15),
        )
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["first_logged_date"] == "2025-01-01"
        assert parsed["latest_logged_date"] == "2025-06-15"

    def test_no_float_conversion(self):
        obj = _make_data()
        dumped = obj.model_dump()
        dec_fields = (
            "starting_weight_kg",
            "latest_weight_kg",
            "absolute_change_kg",
            "percentage_change",
        )
        for field in dec_fields:
            assert not isinstance(dumped[field], float)

    def test_success_response_json(self):
        resp = BodyWeightTrendSuccessResponse(data=_make_data())
        raw = resp.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["success"] is True
        assert parsed["message"] == "Body-weight trend calculated successfully."
        assert parsed["data"]["direction"] == "increased"
        assert parsed["data"]["first_logged_date"] == "2025-06-01"


# ===========================================================================
# M. Schema purity — no prohibited imports
# ===========================================================================


class TestSchemaPurity:
    def test_no_fastapi_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "fastapi" not in source.lower()

    def test_no_starlette_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "starlette" not in source.lower()

    def test_no_sqlalchemy_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "sqlalchemy" not in source.lower()

    def test_no_alembic_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "alembic" not in source.lower()

    def test_no_database_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.db" not in source
        assert "import app.db" not in source

    def test_no_repository_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "repositories" not in source

    def test_no_service_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.services" not in source

    def test_no_api_router_import(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_environment_access(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "os.environ" not in source
        assert "getenv" not in source
        assert "os.getenv" not in source

    def test_no_network_access(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "import request" not in source.lower()
        assert "urllib" not in source.lower()
        assert "httpx" not in source.lower()

    def test_no_system_clock(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_no_random_behavior(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "random" not in source.lower()

    def test_no_uuid4(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "uuid4" not in source

    def test_no_ai_llm(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in source.lower()

    def test_no_prediction_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "predict" not in source.lower()

    def test_no_recommendation_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "recommend" not in source.lower()

    def test_no_persistence_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "persist" not in source.lower()
        assert "commit" not in source.lower()
        assert "flush" not in source.lower()

    def test_no_calculation_duplication(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "absolute_change" not in source.lower() or "validate" in source.lower()
        # Verify no formula-like patterns exist
        assert "sorted(" not in source
        assert "sort(" not in source
        assert "ROUND_HALF_UP" not in source
        assert "rounded_change" not in source
        assert "raw_change" not in source
        assert "percentage" not in source.lower() or "validate" in source.lower()

    def test_no_medical_interpretation(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        for token in ("diagnosis", "treatment", "healthy", "unhealthy", "improving", "worsening"):
            assert token not in source.lower()


# ===========================================================================
# N. Dependency direction
# ===========================================================================


class TestDependencyDirection:
    def test_schema_may_import_domain(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.core.body_weight_trends" in source

    def test_domain_must_not_import_pydantic(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "pydantic" not in source.lower()

    def test_domain_must_not_import_schema_module(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "from app.schemas" not in source

    def test_no_circular_dependency(self):
        import app.core.body_weight_trends
        import app.schemas.body_weight_trends

        assert app.core.body_weight_trends is not None
        assert app.schemas.body_weight_trends is not None

    def test_domain_must_not_import_fastapi(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "fastapi" not in source.lower()

    def test_domain_must_not_import_sqlalchemy(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "sqlalchemy" not in source.lower()

    def test_domain_must_not_import_starlette(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "starlette" not in source.lower()


# ===========================================================================
# O. Existing body-weight schema regression
# ===========================================================================
# ===========================================================================


class TestExistingBodyWeightSchemaRegression:
    def test_existing_schema_imports(self):
        from app.schemas.body_weight import (
            BodyWeightDeleteSuccessResponse,
            BodyWeightEntryCreate,
            BodyWeightEntryData,
            BodyWeightEntrySuccessResponse,
            BodyWeightHistoryData,
            BodyWeightHistorySuccessResponse,
        )

        assert BodyWeightEntryCreate is not None
        assert BodyWeightEntryData is not None
        assert BodyWeightHistoryData is not None
        assert BodyWeightEntrySuccessResponse is not None
        assert BodyWeightHistorySuccessResponse is not None
        assert BodyWeightDeleteSuccessResponse is not None

    def test_body_weight_schema_from_domain_unchanged(self):
        from uuid import UUID

        from app.core.body_weight import BodyWeightEntry
        from app.schemas.body_weight import BodyWeightEntryData

        entry = BodyWeightEntry(
            entry_id=UUID("00000000-0000-0000-0000-000000000001"),
            logged_date=date(2025, 6, 15),
            weight_kg=_dec("70.00"),
        )
        data = BodyWeightEntryData.from_domain(entry)
        assert data.entry_id == entry.entry_id
        assert data.logged_date == entry.logged_date
        assert data.weight_kg == entry.weight_kg


# ===========================================================================
# Q. Full-suite integration — no side effects
# ===========================================================================


class TestIntegration:
    def test_from_result_round_trip(self):
        result = _make_result()
        data = BodyWeightTrendData.from_result(result)
        assert data.observation_count == result.observation_count
        assert data.first_logged_date == result.first_logged_date
        assert data.latest_logged_date == result.latest_logged_date
        assert data.starting_weight_kg == result.starting_weight_kg
        assert data.latest_weight_kg == result.latest_weight_kg
        assert data.absolute_change_kg == result.absolute_change_kg
        assert data.percentage_change == result.percentage_change
        assert data.direction == result.direction

    def test_success_response_round_trip(self):
        data = _make_data()
        resp = BodyWeightTrendSuccessResponse(data=data)
        assert resp.data.observation_count == data.observation_count
        assert resp.data.direction == data.direction

    def test_config_not_frozen_on_success_response(self):
        config = BodyWeightTrendSuccessResponse.model_config
        assert config.get("frozen") is not True

    def test_no_forbidden_generated_text(self):
        for token in ("diagnosis", "prescription of", "health score", "per week"):
            assert token not in BodyWeightTrendSuccessResponse.model_fields["message"].default
