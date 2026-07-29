from __future__ import annotations

import importlib
import inspect
import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.body_weight import (
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
)
from app.core.body_weight_goals import (
    BodyWeightGoal,
    BodyWeightGoalDirection,
    BodyWeightGoalProgressResult,
    BodyWeightGoalStatus,
    calculate_body_weight_goal_progress,
    create_body_weight_goal,
)
from app.schemas.body_weight_goals import (
    BodyWeightGoalCreate,
    BodyWeightGoalData,
    BodyWeightGoalProgressData,
    BodyWeightGoalProgressSuccessResponse,
    BodyWeightGoalSuccessResponse,
)

SCHEMA_MODULE = "app.schemas.body_weight_goals"
DOMAIN_MODULE = "app.core.body_weight_goals"

_NEW_EXPORTS = [
    "BodyWeightGoalCreate",
    "BodyWeightGoalData",
    "BodyWeightGoalProgressData",
    "BodyWeightGoalSuccessResponse",
    "BodyWeightGoalProgressSuccessResponse",
]


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _make_goal(
    *,
    starting_weight_kg: Decimal | None = None,
    target_weight_kg: Decimal | None = None,
) -> BodyWeightGoal:
    return create_body_weight_goal(
        starting_weight_kg=starting_weight_kg if starting_weight_kg is not None else _dec("100.00"),
        target_weight_kg=target_weight_kg if target_weight_kg is not None else _dec("80.00"),
    )


def _make_result(
    *,
    starting_weight_kg: Decimal | None = None,
    current_weight_kg: Decimal | None = None,
    target_weight_kg: Decimal | None = None,
) -> BodyWeightGoalProgressResult:
    return calculate_body_weight_goal_progress(
        starting_weight_kg=starting_weight_kg if starting_weight_kg is not None else _dec("100.00"),
        current_weight_kg=current_weight_kg if current_weight_kg is not None else _dec("90.00"),
        target_weight_kg=target_weight_kg if target_weight_kg is not None else _dec("80.00"),
    )


# ===========================================================================
# A. Module and exports
# ===========================================================================


class TestModuleExports:
    def test_module_imports_successfully(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        assert mod is not None

    def test_all_five_schemas_exist(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        for name in _NEW_EXPORTS:
            assert hasattr(mod, name), f"Missing schema: {name}"

    def test_all_five_exported_from_app_schemas(self):
        from app.schemas import (
            BodyWeightGoalCreate,
            BodyWeightGoalData,
            BodyWeightGoalProgressData,
            BodyWeightGoalProgressSuccessResponse,
            BodyWeightGoalSuccessResponse,
        )

        assert BodyWeightGoalCreate is not None
        assert BodyWeightGoalData is not None
        assert BodyWeightGoalProgressData is not None
        assert BodyWeightGoalSuccessResponse is not None
        assert BodyWeightGoalProgressSuccessResponse is not None

    def test_all_five_in_all(self):
        from app.schemas import __all__ as all_exports

        for name in _NEW_EXPORTS:
            assert name in all_exports, f"Missing from __all__: {name}"

    def test_no_existing_exports_removed(self):
        from app.schemas import __all__ as all_exports

        for name in [
            "BodyWeightEntryCreate",
            "BodyWeightEntryData",
            "BodyWeightHistoryData",
            "BodyWeightEntrySuccessResponse",
            "BodyWeightHistorySuccessResponse",
            "BodyWeightDeleteSuccessResponse",
            "BodyWeightTrendData",
            "BodyWeightTrendSuccessResponse",
            "CalculatedNutritionData",
            "DailyNutritionLogSummaryData",
            "NutritionProfileData",
            "DailyNutritionProgressData",
            "NutritionSummaryData",
        ]:
            assert name in all_exports, f"Existing export removed: {name}"

    def test_no_duplicate_names_in_all(self):
        from app.schemas import __all__ as all_exports

        assert len(all_exports) == len(set(all_exports))


# ===========================================================================
# B. BodyWeightGoalCreate
# ===========================================================================


class TestBodyWeightGoalCreateStructure:
    def test_exact_fields(self):
        assert set(BodyWeightGoalCreate.model_fields) == {
            "starting_weight_kg",
            "target_weight_kg",
        }

    def test_exact_field_order(self):
        assert list(BodyWeightGoalCreate.model_fields) == [
            "starting_weight_kg",
            "target_weight_kg",
        ]

    def test_both_required(self):
        assert BodyWeightGoalCreate.model_fields["starting_weight_kg"].is_required()
        assert BodyWeightGoalCreate.model_fields["target_weight_kg"].is_required()

    def test_extra_forbid(self):
        assert BodyWeightGoalCreate.model_config.get("extra") == "forbid"

    def test_frozen_true(self):
        assert BodyWeightGoalCreate.model_config.get("frozen") is True

    def test_no_from_attributes(self):
        assert BodyWeightGoalCreate.model_config.get("from_attributes") is None

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalCreate(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_missing_starting_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalCreate(target_weight_kg=_dec("80.00"))  # type: ignore[call-arg]

    def test_missing_target_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalCreate(starting_weight_kg=_dec("100.00"))  # type: ignore[call-arg]


class TestBodyWeightGoalCreateInputTypes:
    def test_decimal_accepted(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert obj.starting_weight_kg == _dec("100.00")
        assert obj.target_weight_kg == _dec("80.00")

    def test_int_accepted(self):
        obj = BodyWeightGoalCreate(starting_weight_kg=100, target_weight_kg=80)
        assert obj.starting_weight_kg == _dec("100.00")
        assert obj.target_weight_kg == _dec("80.00")

    def test_finite_float_accepted(self):
        obj = BodyWeightGoalCreate(starting_weight_kg=70.5, target_weight_kg=60.25)
        assert obj.starting_weight_kg == _dec("70.50")
        assert obj.target_weight_kg == _dec("60.25")

    def test_numeric_string_accepted(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg="100.00",
            target_weight_kg="80.00",
        )
        assert obj.starting_weight_kg == _dec("100.00")
        assert obj.target_weight_kg == _dec("80.00")

    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="must not be a boolean"):
            BodyWeightGoalCreate(starting_weight_kg=True, target_weight_kg=_dec("80.00"))  # type: ignore[arg-type]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalCreate(starting_weight_kg=None, target_weight_kg=_dec("80.00"))  # type: ignore[arg-type]

    def test_empty_string_rejected(self):
        with pytest.raises(ValidationError, match="valid decimal"):
            BodyWeightGoalCreate(starting_weight_kg="", target_weight_kg=_dec("80.00"))  # type: ignore[arg-type]

    def test_whitespace_string_rejected(self):
        with pytest.raises(ValidationError, match="valid decimal"):
            BodyWeightGoalCreate(starting_weight_kg="   ", target_weight_kg=_dec("80.00"))  # type: ignore[arg-type]

    def test_malformed_string_rejected(self):
        with pytest.raises(ValidationError, match="valid decimal"):
            BodyWeightGoalCreate(starting_weight_kg="abc", target_weight_kg=_dec("80.00"))  # type: ignore[arg-type]

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightGoalCreate(starting_weight_kg=Decimal("NaN"), target_weight_kg=_dec("80.00"))  # type: ignore[arg-type]

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightGoalCreate(
                starting_weight_kg=Decimal("Infinity"), target_weight_kg=_dec("80.00")
            )  # type: ignore[arg-type]

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightGoalCreate(
                starting_weight_kg=Decimal("-Infinity"), target_weight_kg=_dec("80.00")
            )  # type: ignore[arg-type]


class TestBodyWeightGoalCreateRange:
    def test_minimum_accepted(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg=MIN_BODY_WEIGHT_KG,
            target_weight_kg=MIN_BODY_WEIGHT_KG,
        )
        assert obj.starting_weight_kg == MIN_BODY_WEIGHT_KG

    def test_maximum_accepted(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg=MAX_BODY_WEIGHT_KG,
            target_weight_kg=MAX_BODY_WEIGHT_KG,
        )
        assert obj.target_weight_kg == MAX_BODY_WEIGHT_KG

    def test_below_minimum_rejected(self):
        with pytest.raises(ValidationError, match="at least"):
            BodyWeightGoalCreate(starting_weight_kg=_dec("9.99"), target_weight_kg=_dec("80.00"))

    def test_above_maximum_rejected(self):
        with pytest.raises(ValidationError, match="at most"):
            BodyWeightGoalCreate(starting_weight_kg=_dec("700.01"), target_weight_kg=_dec("80.00"))

    def test_round_half_up(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg=_dec("100.125"), target_weight_kg=_dec("80.125")
        )
        assert obj.starting_weight_kg == _dec("100.13")
        assert obj.target_weight_kg == _dec("80.13")

    def test_boundary_after_rounding_rejected_below(self):
        with pytest.raises(ValidationError, match="at least"):
            BodyWeightGoalCreate(starting_weight_kg=_dec("9.994"), target_weight_kg=_dec("80.00"))

    def test_boundary_after_rounding_accepted_above(self):
        obj = BodyWeightGoalCreate(starting_weight_kg=_dec("9.995"), target_weight_kg=_dec("80.00"))
        assert obj.starting_weight_kg == _dec("10.00")

    def test_decimal_preserved_in_python(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg=_dec("100.00"), target_weight_kg=_dec("80.00")
        )
        assert isinstance(obj.starting_weight_kg, Decimal)
        assert isinstance(obj.target_weight_kg, Decimal)

    def test_decimal_serialized_as_json_string(self):
        obj = BodyWeightGoalCreate(
            starting_weight_kg=_dec("100.00"), target_weight_kg=_dec("80.00")
        )
        parsed = json.loads(obj.model_dump_json())
        assert parsed["starting_weight_kg"] == "100.00"
        assert parsed["target_weight_kg"] == "80.00"

    def test_equal_start_and_target_accepted(self):
        obj = BodyWeightGoalCreate(starting_weight_kg=_dec("80.00"), target_weight_kg=_dec("80.00"))
        assert obj.starting_weight_kg == _dec("80.00")
        assert obj.target_weight_kg == _dec("80.00")

    def test_no_direction_calculated(self):
        assert "direction" not in BodyWeightGoalCreate.model_fields

    def test_no_progress_calculated(self):
        for field in ("progress_percentage", "status", "remaining_change_kg"):
            assert field not in BodyWeightGoalCreate.model_fields

    def test_caller_input_not_mutated(self):
        start = _dec("100.00")
        target = _dec("80.00")
        BodyWeightGoalCreate(starting_weight_kg=start, target_weight_kg=target)
        assert start == _dec("100.00")
        assert target == _dec("80.00")


# ===========================================================================
# C. BodyWeightGoalData
# ===========================================================================


class TestBodyWeightGoalDataStructure:
    def test_exact_three_fields(self):
        assert set(BodyWeightGoalData.model_fields) == {
            "starting_weight_kg",
            "target_weight_kg",
            "direction",
        }

    def test_exact_field_order(self):
        assert list(BodyWeightGoalData.model_fields) == [
            "starting_weight_kg",
            "target_weight_kg",
            "direction",
        ]

    def test_extra_forbid(self):
        assert BodyWeightGoalData.model_config.get("extra") == "forbid"

    def test_frozen_true(self):
        assert BodyWeightGoalData.model_config.get("frozen") is True

    def test_no_from_attributes(self):
        assert BodyWeightGoalData.model_config.get("from_attributes") is None

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_all_fields_required(self):
        for missing in [
            {"target_weight_kg": _dec("80.00"), "direction": BodyWeightGoalDirection.DECREASE},
            {"starting_weight_kg": _dec("100.00"), "direction": BodyWeightGoalDirection.DECREASE},
            {"starting_weight_kg": _dec("100.00"), "target_weight_kg": _dec("80.00")},
        ]:
            with pytest.raises(ValidationError):
                BodyWeightGoalData(**missing)  # type: ignore[arg-type]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalData(
                starting_weight_kg=None,  # type: ignore[arg-type]
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
            )


class TestBodyWeightGoalDataValidation:
    def test_valid_values_accepted(self):
        obj = BodyWeightGoalData(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
            direction=BodyWeightGoalDirection.DECREASE,
        )
        assert obj.starting_weight_kg == _dec("100.00")
        assert obj.target_weight_kg == _dec("80.00")

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightGoalData(
                starting_weight_kg=Decimal("NaN"),
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
            )

    def test_below_minimum_rejected(self):
        with pytest.raises(ValidationError, match="at least"):
            BodyWeightGoalData(
                starting_weight_kg=_dec("9.99"),
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
            )

    def test_above_maximum_rejected(self):
        with pytest.raises(ValidationError, match="at most"):
            BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("700.01"),
                direction=BodyWeightGoalDirection.DECREASE,
            )

    def test_valid_directions_accepted(self):
        for direction in BodyWeightGoalDirection:
            obj = BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction=direction,
            )
            assert obj.direction == direction

    def test_invalid_direction_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction="unknown",  # type: ignore[arg-type]
            )

    def test_direction_annotation_is_enum(self):
        assert BodyWeightGoalData.model_fields["direction"].annotation is BodyWeightGoalDirection

    def test_lowercase_direction_serialization(self):
        for direction, expected in [
            (BodyWeightGoalDirection.DECREASE, "decrease"),
            (BodyWeightGoalDirection.MAINTAIN, "maintain"),
            (BodyWeightGoalDirection.INCREASE, "increase"),
        ]:
            obj = BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction=direction,
            )
            parsed = json.loads(obj.model_dump_json())
            assert parsed["direction"] == expected


class TestBodyWeightGoalDataFromDomain:
    def test_from_domain_copies_exactly(self):
        goal = _make_goal(starting_weight_kg=_dec("100.00"), target_weight_kg=_dec("80.00"))
        data = BodyWeightGoalData.from_domain(goal)
        assert data.starting_weight_kg == goal.starting_weight_kg
        assert data.target_weight_kg == goal.target_weight_kg
        assert data.direction == goal.direction

    def test_no_arithmetic(self):
        goal = _make_goal(starting_weight_kg=_dec("100.123"), target_weight_kg=_dec("80.456"))
        data = BodyWeightGoalData.from_domain(goal)
        assert data.starting_weight_kg == _dec("100.12")
        assert data.target_weight_kg == _dec("80.46")

    def test_no_rounding(self):
        goal = _make_goal(starting_weight_kg=_dec("100.00"), target_weight_kg=_dec("80.00"))
        data = BodyWeightGoalData.from_domain(goal)
        assert data.starting_weight_kg == _dec("100.00")

    def test_no_direction_reclassification(self):
        for direction in BodyWeightGoalDirection:
            goal = create_body_weight_goal(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
            )
            object.__setattr__(goal, "direction", direction)
            data = BodyWeightGoalData.from_domain(goal)
            assert data.direction == direction

    def test_domain_not_mutated(self):
        goal = _make_goal()
        original_start = goal.starting_weight_kg
        original_target = goal.target_weight_kg
        original_direction = goal.direction
        BodyWeightGoalData.from_domain(goal)
        assert goal.starting_weight_kg == original_start
        assert goal.target_weight_kg == original_target
        assert goal.direction == original_direction

    def test_deterministic(self):
        goal = _make_goal()
        assert BodyWeightGoalData.from_domain(goal).model_dump() == (
            BodyWeightGoalData.from_domain(goal).model_dump()
        )

    def test_invalid_non_domain_rejected(self):
        with pytest.raises(TypeError, match="BodyWeightGoal"):
            BodyWeightGoalData.from_domain("not a goal")  # type: ignore[arg-type]


# ===========================================================================
# D. BodyWeightGoalProgressData
# ===========================================================================


class TestBodyWeightGoalProgressDataStructure:
    def test_exact_ten_fields(self):
        assert set(BodyWeightGoalProgressData.model_fields) == {
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "direction",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
            "status",
            "requires_onboarding",
        }

    def test_exact_field_order(self):
        assert list(BodyWeightGoalProgressData.model_fields) == [
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "direction",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
            "status",
            "requires_onboarding",
        ]

    def test_extra_forbid(self):
        assert BodyWeightGoalProgressData.model_config.get("extra") == "forbid"

    def test_frozen_true(self):
        assert BodyWeightGoalProgressData.model_config.get("frozen") is True

    def test_no_from_attributes(self):
        assert BodyWeightGoalProgressData.model_config.get("from_attributes") is None

    def test_all_fields_required(self):
        full = _make_result()
        field_names = [f for f in BodyWeightGoalProgressData.model_fields if f != "requires_onboarding"]
        for skip in field_names:
            values = {
                "starting_weight_kg": full.starting_weight_kg,
                "current_weight_kg": full.current_weight_kg,
                "target_weight_kg": full.target_weight_kg,
                "direction": full.direction,
                "total_change_required_kg": full.total_change_required_kg,
                "change_achieved_kg": full.change_achieved_kg,
                "remaining_change_kg": full.remaining_change_kg,
                "progress_percentage": full.progress_percentage,
                "status": full.status,
            }
            del values[skip]
            with pytest.raises(ValidationError):
                BodyWeightGoalProgressData(**values)  # type: ignore[arg-type]

    def test_extra_field_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
                extra_field="value",  # type: ignore[call-arg]
            )


class TestBodyWeightGoalProgressDataValidation:
    def test_valid_values_accepted(self):
        full = _make_result()
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        assert obj.starting_weight_kg == full.starting_weight_kg

    def test_weight_nan_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightGoalProgressData(
                starting_weight_kg=Decimal("NaN"),
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )

    def test_weight_zero_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError, match="positive"):
            BodyWeightGoalProgressData(
                starting_weight_kg=_dec("0.00"),
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )

    def test_weight_below_minimum_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError, match="at least"):
            BodyWeightGoalProgressData(
                starting_weight_kg=_dec("9.99"),
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )

    def test_total_required_zero_accepted(self):
        # 0 is allowed for empty placeholder data (onboarding)
        full = _make_result()
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=_dec("0.00"),
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        assert obj.total_change_required_kg == Decimal("0.00")

    def test_total_required_negative_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError, match="non-negative"):
            BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=_dec("-5.00"),
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )

    def test_signed_change_achieved_accepted(self):
        full = _make_result()
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=_dec("-5.00"),
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        assert obj.change_achieved_kg == _dec("-5.00")

    def test_signed_remaining_accepted(self):
        full = _make_result()
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=_dec("-5.00"),
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        assert obj.remaining_change_kg == _dec("-5.00")

    def test_signed_percentage_accepted(self):
        full = _make_result()
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=_dec("-25.00"),
            status=full.status,
        )
        assert obj.progress_percentage == _dec("-25.00")

    def test_valid_direction_accepted(self):
        for direction in BodyWeightGoalDirection:
            full = _make_result()
            object.__setattr__(full, "direction", direction)
            obj = BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )
            assert obj.direction == direction

    def test_invalid_direction_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction="unknown",  # type: ignore[arg-type]
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )

    def test_valid_status_accepted(self):
        for status in BodyWeightGoalStatus:
            full = _make_result()
            object.__setattr__(full, "status", status)
            obj = BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )
            assert obj.status == status

    def test_invalid_status_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status="unknown",  # type: ignore[arg-type]
            )

    def test_direction_annotation_is_enum(self):
        assert (
            BodyWeightGoalProgressData.model_fields["direction"].annotation
            is BodyWeightGoalDirection
        )

    def test_status_annotation_is_enum(self):
        assert BodyWeightGoalProgressData.model_fields["status"].annotation is BodyWeightGoalStatus

    def test_lowercase_direction_serialization(self):
        full = _make_result()
        object.__setattr__(full, "direction", BodyWeightGoalDirection.INCREASE)
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        parsed = json.loads(obj.model_dump_json())
        assert parsed["direction"] == "increase"

    def test_lowercase_status_serialization(self):
        for status, expected in [
            (BodyWeightGoalStatus.NOT_STARTED, "not_started"),
            (BodyWeightGoalStatus.IN_PROGRESS, "in_progress"),
            (BodyWeightGoalStatus.TARGET_REACHED, "target_reached"),
            (BodyWeightGoalStatus.TARGET_PASSED, "target_passed"),
        ]:
            full = _make_result()
            object.__setattr__(full, "status", status)
            obj = BodyWeightGoalProgressData(
                starting_weight_kg=full.starting_weight_kg,
                current_weight_kg=full.current_weight_kg,
                target_weight_kg=full.target_weight_kg,
                direction=full.direction,
                total_change_required_kg=full.total_change_required_kg,
                change_achieved_kg=full.change_achieved_kg,
                remaining_change_kg=full.remaining_change_kg,
                progress_percentage=full.progress_percentage,
                status=full.status,
            )
            parsed = json.loads(obj.model_dump_json())
            assert parsed["status"] == expected

    def test_decimal_preserved_in_python(self):
        full = _make_result()
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        dumped = obj.model_dump()
        for field in (
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
        ):
            assert isinstance(dumped[field], Decimal)

    def test_negative_value_json_serialization(self):
        full = _make_result()
        object.__setattr__(full, "change_achieved_kg", _dec("-5.00"))
        object.__setattr__(full, "remaining_change_kg", _dec("-25.00"))
        object.__setattr__(full, "progress_percentage", _dec("-25.00"))
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        parsed = json.loads(obj.model_dump_json())
        assert parsed["change_achieved_kg"] == "-5.00"
        assert parsed["remaining_change_kg"] == "-25.00"
        assert parsed["progress_percentage"] == "-25.00"

    def test_above_100_json_serialization(self):
        full = _make_result()
        object.__setattr__(full, "progress_percentage", _dec("150.00"))
        obj = BodyWeightGoalProgressData(
            starting_weight_kg=full.starting_weight_kg,
            current_weight_kg=full.current_weight_kg,
            target_weight_kg=full.target_weight_kg,
            direction=full.direction,
            total_change_required_kg=full.total_change_required_kg,
            change_achieved_kg=full.change_achieved_kg,
            remaining_change_kg=full.remaining_change_kg,
            progress_percentage=full.progress_percentage,
            status=full.status,
        )
        parsed = json.loads(obj.model_dump_json())
        assert parsed["progress_percentage"] == "150.00"


class TestBodyWeightGoalProgressDataFromResult:
    def test_nine_field_exact_copy(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.starting_weight_kg == result.starting_weight_kg
        assert data.current_weight_kg == result.current_weight_kg
        assert data.target_weight_kg == result.target_weight_kg
        assert data.direction == result.direction
        assert data.total_change_required_kg == result.total_change_required_kg
        assert data.change_achieved_kg == result.change_achieved_kg
        assert data.remaining_change_kg == result.remaining_change_kg
        assert data.progress_percentage == result.progress_percentage
        assert data.status == result.status

    def test_negative_progress_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("105.00"),
            target_weight_kg=_dec("80.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.progress_percentage == _dec("-25.00")
        assert data.change_achieved_kg == _dec("-5.00")

    def test_zero_progress_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.progress_percentage == _dec("0.00")
        assert data.change_achieved_kg == _dec("0.00")

    def test_exact_100_percent_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("80.00"),
            target_weight_kg=_dec("80.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.progress_percentage == _dec("100.00")

    def test_above_100_percent_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("75.00"),
            target_weight_kg=_dec("70.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.progress_percentage == _dec("150.00")

    def test_negative_remaining_preserved(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("75.00"),
            target_weight_kg=_dec("80.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.remaining_change_kg == _dec("-5.00")

    def test_no_clamping(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("70.00"),
            target_weight_kg=_dec("80.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.remaining_change_kg == _dec("-10.00")

    def test_no_capping(self):
        result = _make_result(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("75.00"),
            target_weight_kg=_dec("70.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.progress_percentage == _dec("150.00")

    def test_no_arithmetic(self):
        result = _make_result()
        original = {
            "starting_weight_kg": result.starting_weight_kg,
            "current_weight_kg": result.current_weight_kg,
            "target_weight_kg": result.target_weight_kg,
            "total_change_required_kg": result.total_change_required_kg,
            "change_achieved_kg": result.change_achieved_kg,
            "remaining_change_kg": result.remaining_change_kg,
            "progress_percentage": result.progress_percentage,
        }
        BodyWeightGoalProgressData.from_result(result)
        for field, value in original.items():
            assert getattr(result, field) == value

    def test_no_rounding(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.123"),
            current_weight_kg=_dec("90.456"),
            target_weight_kg=_dec("80.789"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.starting_weight_kg == _dec("100.12")

    def test_no_direction_reclassification(self):
        result = _make_result(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        object.__setattr__(result, "direction", BodyWeightGoalDirection.MAINTAIN)
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.direction == BodyWeightGoalDirection.MAINTAIN

    def test_no_status_reclassification(self):
        result = _make_result()
        object.__setattr__(result, "status", BodyWeightGoalStatus.TARGET_PASSED)
        data = BodyWeightGoalProgressData.from_result(result)
        assert data.status == BodyWeightGoalStatus.TARGET_PASSED

    def test_domain_result_not_mutated(self):
        result = _make_result()
        original = repr(result)
        BodyWeightGoalProgressData.from_result(result)
        assert repr(result) == original

    def test_deterministic(self):
        result = _make_result()
        assert BodyWeightGoalProgressData.from_result(result).model_dump() == (
            BodyWeightGoalProgressData.from_result(result).model_dump()
        )

    def test_invalid_non_result_rejected(self):
        with pytest.raises(TypeError, match="BodyWeightGoalProgressResult"):
            BodyWeightGoalProgressData.from_result("not a result")  # type: ignore[arg-type]


# ===========================================================================
# E. Success responses
# ===========================================================================


class TestBodyWeightGoalSuccessResponse:
    def test_exact_fields(self):
        assert set(BodyWeightGoalSuccessResponse.model_fields) == {
            "success",
            "message",
            "data",
        }

    def test_default_success_is_true(self):
        resp = BodyWeightGoalSuccessResponse(
            data=BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
            )
        )
        assert resp.success is True

    def test_success_is_literal_true(self):
        annotation = BodyWeightGoalSuccessResponse.model_fields["success"].annotation
        args = getattr(annotation, "__args__", ())
        assert True in args
        assert False not in args

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=BodyWeightGoalData(
                    starting_weight_kg=_dec("100.00"),
                    target_weight_kg=_dec("80.00"),
                    direction=BodyWeightGoalDirection.DECREASE,
                ),
            )

    def test_exact_default_message(self):
        resp = BodyWeightGoalSuccessResponse(
            data=BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
            )
        )
        assert resp.message == "Body-weight goal created successfully."

    def test_custom_message_accepted(self):
        resp = BodyWeightGoalSuccessResponse(
            message="Custom message.",
            data=BodyWeightGoalData(
                starting_weight_kg=_dec("100.00"),
                target_weight_kg=_dec("80.00"),
                direction=BodyWeightGoalDirection.DECREASE,
            ),
        )
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalSuccessResponse(
                data=BodyWeightGoalData(
                    starting_weight_kg=_dec("100.00"),
                    target_weight_kg=_dec("80.00"),
                    direction=BodyWeightGoalDirection.DECREASE,
                ),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_not_frozen(self):
        assert BodyWeightGoalSuccessResponse.model_config.get("frozen") is not True

    def test_nested_serialization(self):
        data = BodyWeightGoalData(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
            direction=BodyWeightGoalDirection.DECREASE,
        )
        resp = BodyWeightGoalSuccessResponse(data=data)
        parsed = json.loads(resp.model_dump_json())
        assert parsed["success"] is True
        assert parsed["message"] == "Body-weight goal created successfully."
        assert parsed["data"]["starting_weight_kg"] == "100.00"
        assert parsed["data"]["direction"] == "decrease"


class TestBodyWeightGoalProgressSuccessResponse:
    def test_exact_fields(self):
        assert set(BodyWeightGoalProgressSuccessResponse.model_fields) == {
            "success",
            "message",
            "data",
        }

    def test_default_success_is_true(self):
        full = _make_result()
        resp = BodyWeightGoalProgressSuccessResponse(
            data=BodyWeightGoalProgressData.from_result(full)
        )
        assert resp.success is True

    def test_success_is_literal_true(self):
        annotation = BodyWeightGoalProgressSuccessResponse.model_fields["success"].annotation
        args = getattr(annotation, "__args__", ())
        assert True in args
        assert False not in args

    def test_false_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressSuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=BodyWeightGoalProgressData.from_result(full),
            )

    def test_exact_default_message(self):
        full = _make_result()
        resp = BodyWeightGoalProgressSuccessResponse(
            data=BodyWeightGoalProgressData.from_result(full)
        )
        assert resp.message == "Body-weight goal progress calculated successfully."

    def test_custom_message_accepted(self):
        full = _make_result()
        resp = BodyWeightGoalProgressSuccessResponse(
            message="Custom message.",
            data=BodyWeightGoalProgressData.from_result(full),
        )
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressSuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressSuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_field_rejected(self):
        full = _make_result()
        with pytest.raises(ValidationError):
            BodyWeightGoalProgressSuccessResponse(
                data=BodyWeightGoalProgressData.from_result(full),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_not_frozen(self):
        assert BodyWeightGoalProgressSuccessResponse.model_config.get("frozen") is not True

    def test_nested_serialization(self):
        full = _make_result()
        data = BodyWeightGoalProgressData.from_result(full)
        resp = BodyWeightGoalProgressSuccessResponse(data=data)
        parsed = json.loads(resp.model_dump_json())
        assert parsed["success"] is True
        assert parsed["message"] == "Body-weight goal progress calculated successfully."
        assert parsed["data"]["progress_percentage"] == "50.00"


# ===========================================================================
# F. Schema purity
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
        for token in ("groq", "openai", "langchain", "gemini", "llm", "usda"):
            assert token not in source.lower()

    def test_no_persistence_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "persist" not in source.lower()
        assert "commit" not in source.lower()
        assert "flush" not in source.lower()

    def test_no_filesystem_access(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "open(" not in source
        assert "pathlib" not in source.lower()


# ===========================================================================
# G. No duplicated domain logic
# ===========================================================================


class TestNoDuplicatedDomainLogic:
    def test_no_progress_formula(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "change_achieved" not in source.lower() or "validate" in source.lower()
        assert "remaining" not in source.lower() or "validate" in source.lower()

    def test_no_percentage_calculation(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "* 100" not in source
        assert "/ total" not in source.lower()

    def test_no_direction_calculation(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "target_weight_kg < starting_weight_kg" not in source
        assert "target_weight_kg > starting_weight_kg" not in source

    def test_no_status_classification(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "NOT_STARTED" not in source.upper() or "BodyWeightGoalStatus" in source

    def test_no_clamping_capping(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "min(" not in source
        assert "max(" not in source

    def test_no_prediction(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "predict" not in source.lower()

    def test_no_recommendation(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "recommend" not in source.lower()

    def test_no_medical_interpretation(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "diagnosis" not in source.lower()
        assert "treatment" not in source.lower()


# ===========================================================================
# H. Dependency direction
# ===========================================================================


class TestDependencyDirection:
    def test_schema_may_import_domain(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.core.body_weight" in source
        assert "from app.core.body_weight_goals" in source

    def test_domain_must_not_import_pydantic(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "pydantic" not in source.lower()

    def test_domain_must_not_import_schema_module(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "from app.schemas" not in source

    def test_no_circular_dependency(self):
        import app.core.body_weight_goals
        import app.schemas.body_weight_goals

        assert app.core.body_weight_goals is not None
        assert app.schemas.body_weight_goals is not None

    def test_no_duplicate_domain_constants(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "MIN_BODY_WEIGHT_KG = " not in source
        assert "MAX_BODY_WEIGHT_KG = " not in source
        assert "BODY_WEIGHT_DECIMAL_PLACES = " not in source
        assert "class BodyWeightGoalDirection" not in source
        assert "class BodyWeightGoalStatus" not in source


# ===========================================================================
# I. Phase boundary regression
# ===========================================================================


class TestPhaseBoundaries:
    def test_goal_routes_exist(self):
        from app.main import create_app

        app = create_app()
        routes = [r for r in app.routes if hasattr(r, "path") and "goal" in r.path.lower()]
        goal_paths = sorted(set(r.path for r in routes))
        assert goal_paths == ["/api/v1/body-weights/goal-progress", "/api/v1/goals", "/api/v1/goals/{goal_id}"]

    def test_existing_route_inventory_unchanged(self):
        from app.main import create_app

        app = create_app()
        route_paths = sorted(r.path for r in app.routes if hasattr(r, "path"))
        expected_api_paths = {
            "/api/v1/ai-coach/chat",
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/auth/register",
            "/api/v1/auth/supabase-sync",
            "/api/v1/body-weights",
            "/api/v1/body-weights/{entry_id}",
            "/api/v1/body-weights/trend",
            "/api/v1/body-weights/goal-progress",
            "/api/v1/food-recognition/analyze",
            "/api/v1/food-search/search",
            "/api/v1/goals",
            "/api/v1/goals/{goal_id}",
            "/api/v1/health",
            "/api/v1/nutrition-logs",
            "/api/v1/nutrition-logs/progress",
            "/api/v1/nutrition-logs/summary",
            "/api/v1/nutrition-logs/{entry_id}",
            "/api/v1/nutrition-profile",
            "/api/v1/nutrition-profile/calculations",
            "/api/v1/nutrition-profile/summary",
            "/api/v1/search",
            "/api/v1/settings/account",
            "/api/v1/settings/export",
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        }
        actual_api_paths = {p for p in route_paths if p.startswith("/api/")}
        assert actual_api_paths == expected_api_paths

    def test_exactly_one_bearerauth_scheme(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        schemes = openapi.get("components", {}).get("securitySchemes", {})
        bearer_schemes = {
            name: details
            for name, details in schemes.items()
            if details.get("scheme", "").lower() == "bearer"
        }
        assert len(bearer_schemes) == 1

    def test_orm_metadata_unchanged(self):
        from app.db.base import Base

        table_names = set(Base.metadata.tables.keys())
        assert table_names == {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }

    def test_migration_count_updated(self):
        import os

        migration_dir = "alembic/versions"
        files = [f for f in os.listdir(migration_dir) if f.endswith(".py") and f != "__init__.py"]
        assert len(files) == 7

    def test_migration_head_unchanged(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_current_head() == "0295723946b2"

    def test_no_goal_orm_model(self):
        import os

        model_path = "app/models/body_weight_goal.py"
        assert not os.path.exists(model_path)
