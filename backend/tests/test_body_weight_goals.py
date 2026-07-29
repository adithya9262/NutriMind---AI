from __future__ import annotations

import importlib.util
from dataclasses import FrozenInstanceError
from decimal import Decimal, getcontext

import pytest

from app.core import body_weight_goals as mod
from app.core.body_weight import (
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
)
from app.core.body_weight_goal_exceptions import (
    BodyWeightGoalError,
    InvalidBodyWeightGoalProgressError,
)
from app.core.body_weight_goals import (
    BodyWeightGoal,
    BodyWeightGoalDirection,
    BodyWeightGoalProgressResult,
    BodyWeightGoalStatus,
    calculate_body_weight_goal_progress,
    create_body_weight_goal,
)

MODULE = "app.core.body_weight_goals"

_PROHIBITED = {
    "fastapi",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "alembic",
    "http",
    "os",
    "requests",
    "httpx",
    "urllib",
}


def _dec(value: str) -> Decimal:
    return Decimal(value)


# ===========================================================================
# B. Enum contracts
# ===========================================================================


class TestGoalDirectionEnum:
    def test_exact_members(self):
        assert set(BodyWeightGoalDirection.__members__.keys()) == {
            "DECREASE",
            "MAINTAIN",
            "INCREASE",
        }

    def test_exact_member_count(self):
        assert len(BodyWeightGoalDirection) == 3

    def test_exact_values(self):
        assert BodyWeightGoalDirection.DECREASE == "decrease"
        assert BodyWeightGoalDirection.MAINTAIN == "maintain"
        assert BodyWeightGoalDirection.INCREASE == "increase"

    def test_str_enum_behavior(self):
        assert isinstance(BodyWeightGoalDirection.DECREASE, str)
        assert BodyWeightGoalDirection.DECREASE == "decrease"

    def test_json_friendly_lowercase(self):
        for member in BodyWeightGoalDirection:
            assert member.value == member.value.lower()

    def test_no_health_or_medical_labels(self):
        joined = " ".join(BodyWeightGoalDirection.__members__.keys()).lower()
        for label in ("healthy", "unhealthy", "good", "bad", "improving", "worsening"):
            assert label not in joined


class TestGoalStatusEnum:
    def test_exact_members(self):
        assert set(BodyWeightGoalStatus.__members__.keys()) == {
            "NOT_STARTED",
            "IN_PROGRESS",
            "TARGET_REACHED",
            "TARGET_PASSED",
        }

    def test_exact_member_count(self):
        assert len(BodyWeightGoalStatus) == 4

    def test_exact_values(self):
        assert BodyWeightGoalStatus.NOT_STARTED == "not_started"
        assert BodyWeightGoalStatus.IN_PROGRESS == "in_progress"
        assert BodyWeightGoalStatus.TARGET_REACHED == "target_reached"
        assert BodyWeightGoalStatus.TARGET_PASSED == "target_passed"

    def test_str_enum_behavior(self):
        assert isinstance(BodyWeightGoalStatus.IN_PROGRESS, str)

    def test_json_friendly_lowercase(self):
        for member in BodyWeightGoalStatus:
            assert member.value == member.value.lower()

    def test_no_health_or_medical_labels(self):
        joined = " ".join(BodyWeightGoalStatus.__members__.keys()).lower()
        for label in (
            "on_track",
            "off_track",
            "healthy",
            "unhealthy",
            "successful",
            "failed",
            "warning",
            "risk",
        ):
            assert label not in joined


# ===========================================================================
# C. Dataclass contracts
# ===========================================================================


class TestGoalDataclass:
    def test_exact_fields(self):
        assert list(BodyWeightGoal.__dataclass_fields__.keys()) == [
            "starting_weight_kg",
            "target_weight_kg",
            "direction",
        ]

    def test_exact_field_order(self):
        fields = list(BodyWeightGoal.__dataclass_fields__.keys())
        assert fields == ["starting_weight_kg", "target_weight_kg", "direction"]

    def test_frozen(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        with pytest.raises(FrozenInstanceError):
            goal.starting_weight_kg = _dec("90.00")

    def test_slots(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
            goal.some_new_attribute = _dec("1.00")


class TestProgressResultDataclass:
    def test_exact_fields(self):
        assert list(BodyWeightGoalProgressResult.__dataclass_fields__.keys()) == [
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "direction",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
            "status",
        ]

    def test_exact_field_order(self):
        fields = list(BodyWeightGoalProgressResult.__dataclass_fields__.keys())
        assert fields == [
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "direction",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
            "status",
        ]

    def test_frozen(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        with pytest.raises(FrozenInstanceError):
            result.status = BodyWeightGoalStatus.TARGET_REACHED

    def test_slots(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
            result.extra = _dec("1.00")


# ===========================================================================
# D. Weight validation
# ===========================================================================


class TestWeightValidation:
    def test_valid_minimum(self):
        goal = create_body_weight_goal(
            starting_weight_kg=MIN_BODY_WEIGHT_KG,
            target_weight_kg=_dec("20.00"),
        )
        assert goal.starting_weight_kg == MIN_BODY_WEIGHT_KG

    def test_valid_maximum(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("20.00"),
            target_weight_kg=MAX_BODY_WEIGHT_KG,
        )
        assert goal.target_weight_kg == MAX_BODY_WEIGHT_KG

    def test_normal_values(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert goal.starting_weight_kg == _dec("100.00")
        assert goal.target_weight_kg == _dec("80.00")

    def test_quantization(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.123"),
            target_weight_kg=_dec("80.456"),
        )
        assert goal.starting_weight_kg == _dec("100.12")
        assert goal.target_weight_kg == _dec("80.46")

    def test_round_half_up(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.005"),
            target_weight_kg=_dec("80.005"),
        )
        assert goal.starting_weight_kg == _dec("100.01")
        assert goal.target_weight_kg == _dec("80.01")

    def test_boundary_after_rounding_below(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=_dec("9.994"),
                target_weight_kg=_dec("20.00"),
            )

    def test_boundary_after_rounding_above(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=_dec("20.00"),
                target_weight_kg=_dec("700.005"),
            )

    def test_reject_bool(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=True,  # type: ignore[arg-type]
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_int(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=100,  # type: ignore[arg-type]
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_float(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=100.0,  # type: ignore[arg-type]
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_string(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg="100.00",  # type: ignore[arg-type]
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_none(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=None,  # type: ignore[arg-type]
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_nan(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=Decimal("nan"),
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_infinity(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=Decimal("inf"),
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_negative_infinity(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=Decimal("-inf"),
                target_weight_kg=_dec("80.00"),
            )

    def test_reject_below_minimum(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=_dec("9.99"),
                target_weight_kg=_dec("20.00"),
            )

    def test_reject_above_maximum(self):
        with pytest.raises(BodyWeightGoalError):
            create_body_weight_goal(
                starting_weight_kg=_dec("20.00"),
                target_weight_kg=_dec("700.01"),
            )


# ===========================================================================
# E. Goal creation
# ===========================================================================


class TestGoalCreation:
    def test_decrease_direction(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert goal.direction is BodyWeightGoalDirection.DECREASE

    def test_increase_direction(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("60.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert goal.direction is BodyWeightGoalDirection.INCREASE

    def test_maintain_direction(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("80.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert goal.direction is BodyWeightGoalDirection.MAINTAIN

    def test_exact_returned_values(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert goal.starting_weight_kg == _dec("100.00")
        assert goal.target_weight_kg == _dec("80.00")
        assert goal.direction is BodyWeightGoalDirection.DECREASE

    def test_quantized_values(self):
        goal = create_body_weight_goal(
            starting_weight_kg=_dec("100.125"),
            target_weight_kg=_dec("80.124"),
        )
        assert goal.starting_weight_kg == _dec("100.13")
        assert goal.target_weight_kg == _dec("80.12")

    def test_keyword_only_signature(self):
        with pytest.raises(TypeError):
            create_body_weight_goal(_dec("100.00"), _dec("80.00"))  # type: ignore[call-arg]

    def test_determinism(self):
        goal_a = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        goal_b = create_body_weight_goal(
            starting_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert goal_a == goal_b

    def test_no_mutation_of_inputs(self):
        start = _dec("100.00")
        target = _dec("80.00")
        create_body_weight_goal(
            starting_weight_kg=start,
            target_weight_kg=target,
        )
        assert start == _dec("100.00")
        assert target == _dec("80.00")


# ===========================================================================
# F. Progress calculation
# ===========================================================================


class TestProgressExamples:
    def test_example_1_decrease_in_progress(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.direction is BodyWeightGoalDirection.DECREASE
        assert result.total_change_required_kg == _dec("20.00")
        assert result.change_achieved_kg == _dec("10.00")
        assert result.remaining_change_kg == _dec("10.00")
        assert result.progress_percentage == _dec("50.00")
        assert result.status is BodyWeightGoalStatus.IN_PROGRESS

    def test_example_2_decrease_target_reached(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("80.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.progress_percentage == _dec("100.00")
        assert result.status is BodyWeightGoalStatus.TARGET_REACHED

    def test_example_3_decrease_target_passed(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("75.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.change_achieved_kg == _dec("25.00")
        assert result.remaining_change_kg == _dec("-5.00")
        assert result.progress_percentage == _dec("125.00")
        assert result.status is BodyWeightGoalStatus.TARGET_PASSED

    def test_example_4_decrease_moved_away(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("105.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.change_achieved_kg == _dec("-5.00")
        assert result.remaining_change_kg == _dec("25.00")
        assert result.progress_percentage == _dec("-25.00")
        assert result.status is BodyWeightGoalStatus.NOT_STARTED

    def test_example_5_increase_in_progress(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("65.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert result.direction is BodyWeightGoalDirection.INCREASE
        assert result.total_change_required_kg == _dec("10.00")
        assert result.change_achieved_kg == _dec("5.00")
        assert result.remaining_change_kg == _dec("5.00")
        assert result.progress_percentage == _dec("50.00")
        assert result.status is BodyWeightGoalStatus.IN_PROGRESS

    def test_example_6_increase_target_passed(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("75.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert result.change_achieved_kg == _dec("15.00")
        assert result.remaining_change_kg == _dec("-5.00")
        assert result.progress_percentage == _dec("150.00")
        assert result.status is BodyWeightGoalStatus.TARGET_PASSED

    def test_example_7_at_starting_weight(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("100.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.change_achieved_kg == _dec("0.00")
        assert result.remaining_change_kg == _dec("20.00")
        assert result.progress_percentage == _dec("0.00")
        assert result.status is BodyWeightGoalStatus.NOT_STARTED


class TestProgressBehavior:
    def test_decrease_not_started(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("102.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.status is BodyWeightGoalStatus.NOT_STARTED

    def test_decrease_in_progress(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.status is BodyWeightGoalStatus.IN_PROGRESS

    def test_decrease_target_reached(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("80.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.status is BodyWeightGoalStatus.TARGET_REACHED

    def test_decrease_target_passed(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("79.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.status is BodyWeightGoalStatus.TARGET_PASSED

    def test_increase_not_started(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("58.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert result.status is BodyWeightGoalStatus.NOT_STARTED

    def test_increase_in_progress(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("65.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert result.status is BodyWeightGoalStatus.IN_PROGRESS

    def test_increase_target_reached(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("70.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert result.status is BodyWeightGoalStatus.TARGET_REACHED

    def test_increase_target_passed(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("60.00"),
            current_weight_kg=_dec("71.00"),
            target_weight_kg=_dec("70.00"),
        )
        assert result.status is BodyWeightGoalStatus.TARGET_PASSED

    def test_no_clamping_remaining_negative(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("70.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert result.remaining_change_kg == _dec("-10.00")

    def test_percentage_round_half_up(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("99.99"),
            target_weight_kg=_dec("98.40"),
        )
        assert result.progress_percentage == _dec("0.63")

    def test_weight_quantization_in_result(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=_dec("100.123"),
            current_weight_kg=_dec("90.456"),
            target_weight_kg=_dec("80.789"),
        )
        assert result.starting_weight_kg == _dec("100.12")
        assert result.current_weight_kg == _dec("90.46")
        assert result.target_weight_kg == _dec("80.79")

    def test_keyword_only_signature(self):
        with pytest.raises(TypeError):
            calculate_body_weight_goal_progress(  # type: ignore[call-arg]
                _dec("100.00"), _dec("90.00"), _dec("80.00")
            )

    def test_determinism(self):
        args = dict(
            starting_weight_kg=_dec("100.00"),
            current_weight_kg=_dec("90.00"),
            target_weight_kg=_dec("80.00"),
        )
        assert calculate_body_weight_goal_progress(**args) == (
            calculate_body_weight_goal_progress(**args)
        )

    def test_no_mutation_of_inputs(self):
        start = _dec("100.00")
        current = _dec("90.00")
        target = _dec("80.00")
        calculate_body_weight_goal_progress(
            starting_weight_kg=start,
            current_weight_kg=current,
            target_weight_kg=target,
        )
        assert start == _dec("100.00")
        assert current == _dec("90.00")
        assert target == _dec("80.00")


# ===========================================================================
# H. Equal start and target
# ===========================================================================


class TestEqualStartTarget:
    def test_raises_progress_error(self):
        with pytest.raises(InvalidBodyWeightGoalProgressError):
            calculate_body_weight_goal_progress(
                starting_weight_kg=_dec("80.00"),
                current_weight_kg=_dec("80.00"),
                target_weight_kg=_dec("80.00"),
            )

    def test_exact_message(self):
        with pytest.raises(InvalidBodyWeightGoalProgressError) as exc_info:
            calculate_body_weight_goal_progress(
                starting_weight_kg=_dec("80.00"),
                current_weight_kg=_dec("80.00"),
                target_weight_kg=_dec("80.00"),
            )
        assert exc_info.value.args[0] == (
            "Body-weight goal progress requires a starting weight that differs "
            "from the target weight."
        )

    def test_no_fallback(self):
        try:
            calculate_body_weight_goal_progress(
                starting_weight_kg=_dec("80.00"),
                current_weight_kg=_dec("80.00"),
                target_weight_kg=_dec("80.00"),
            )
        except InvalidBodyWeightGoalProgressError:
            pass
        else:
            raise AssertionError("Expected InvalidBodyWeightGoalProgressError")

    def test_no_divide_by_zero_leak(self):
        with pytest.raises(InvalidBodyWeightGoalProgressError) as exc_info:
            calculate_body_weight_goal_progress(
                starting_weight_kg=_dec("80.00"),
                current_weight_kg=_dec("80.00"),
                target_weight_kg=_dec("80.00"),
            )
        assert "division" not in str(exc_info.value).lower()
        assert "zero" not in str(exc_info.value).lower()


# ===========================================================================
# G. Purity
# ===========================================================================


class TestPurity:
    def test_no_prohibited_imports(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in _PROHIBITED:
            assert token not in text, f"Prohibited import token: {token}"

    def test_no_system_clock(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in ("datetime.now", "date.today", "utcnow", "today()"):
            assert token not in text, f"System clock usage: {token}"

    def test_no_environment_access(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in ("os.environ", "getenv", "environ["):
            assert token not in text, f"Environment access: {token}"

    def test_no_network(self):
        assert "requests" not in MODULE
        assert "httpx" not in MODULE

    def test_no_filesystem(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in ("open(", "pathlib", "os.path"):
            assert token not in text, f"Filesystem usage: {token}"

    def test_no_database(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in ("session", "engine", "connection", "commit", "select("):
            assert token not in text, f"Database usage: {token}"

    def test_no_framework(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in ("fastapi", "starlette", "apirouter", "depends"):
            assert token not in text, f"Framework usage: {token}"

    def test_no_float_conversion(self):
        source = importlib.util.find_spec(MODULE)
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        assert "float(" not in text, "float conversion present"

    def test_decimal_context_high_precision(self):
        assert getcontext().prec >= 28

    def test_no_prediction(self):
        names = dir(mod)
        for token in ("predict", "projection", "estimate", "rate"):
            assert not any(token in n.lower() for n in names), f"Found {token}"

    def test_no_recommendation(self):
        names = dir(mod)
        for token in ("recommend", "suggest", "advise"):
            assert not any(token in n.lower() for n in names), f"Found {token}"

    def test_no_medical_interpretation(self):
        names = dir(mod)
        for token in ("health", "medical", "bmi", "risk"):
            assert not any(token in n.lower() for n in names), f"Found {token}"
