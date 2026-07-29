from __future__ import annotations

import enum
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.core.body_weight import (
    BODY_WEIGHT_DECIMAL_PLACES,
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
)
from app.core.body_weight_goal_exceptions import (
    BodyWeightGoalError,
    InvalidBodyWeightGoalProgressError,
)

_INVALID_GOAL_WEIGHT_MESSAGE = (
    "Body-weight goal weights must be finite Decimal values within the supported range."
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BODY_WEIGHT_GOAL_PERCENTAGE_DECIMAL_PLACES: Decimal = Decimal("0.01")

# ---------------------------------------------------------------------------
# Goal direction
# ---------------------------------------------------------------------------


class BodyWeightGoalDirection(enum.StrEnum):
    DECREASE = "decrease"
    MAINTAIN = "maintain"
    INCREASE = "increase"


# ---------------------------------------------------------------------------
# Goal status
# ---------------------------------------------------------------------------


class BodyWeightGoalStatus(enum.StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    TARGET_REACHED = "target_reached"
    TARGET_PASSED = "target_passed"


# ---------------------------------------------------------------------------
# Goal definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BodyWeightGoal:
    starting_weight_kg: Decimal
    target_weight_kg: Decimal
    direction: BodyWeightGoalDirection


# ---------------------------------------------------------------------------
# Goal progress result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BodyWeightGoalProgressResult:
    starting_weight_kg: Decimal
    current_weight_kg: Decimal
    target_weight_kg: Decimal
    direction: BodyWeightGoalDirection
    total_change_required_kg: Decimal
    change_achieved_kg: Decimal
    remaining_change_kg: Decimal
    progress_percentage: Decimal
    status: BodyWeightGoalStatus


# ---------------------------------------------------------------------------
# Weight validation
# ---------------------------------------------------------------------------


def _validate_goal_weight(value: object) -> Decimal:
    if isinstance(value, bool):
        raise BodyWeightGoalError(_INVALID_GOAL_WEIGHT_MESSAGE)

    if isinstance(value, Decimal):
        pass
    else:
        raise BodyWeightGoalError(_INVALID_GOAL_WEIGHT_MESSAGE)

    if not value.is_finite():
        raise BodyWeightGoalError(_INVALID_GOAL_WEIGHT_MESSAGE)

    normalized = value.quantize(BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP)

    if normalized < MIN_BODY_WEIGHT_KG:
        raise BodyWeightGoalError(_INVALID_GOAL_WEIGHT_MESSAGE)
    if normalized > MAX_BODY_WEIGHT_KG:
        raise BodyWeightGoalError(_INVALID_GOAL_WEIGHT_MESSAGE)

    return normalized


def _determine_direction(
    *,
    starting_weight_kg: Decimal,
    target_weight_kg: Decimal,
) -> BodyWeightGoalDirection:
    if target_weight_kg < starting_weight_kg:
        return BodyWeightGoalDirection.DECREASE
    if target_weight_kg > starting_weight_kg:
        return BodyWeightGoalDirection.INCREASE
    return BodyWeightGoalDirection.MAINTAIN


# ---------------------------------------------------------------------------
# Goal creation
# ---------------------------------------------------------------------------


def create_body_weight_goal(
    *,
    starting_weight_kg: Decimal,
    target_weight_kg: Decimal,
) -> BodyWeightGoal:
    validated_starting = _validate_goal_weight(starting_weight_kg)
    validated_target = _validate_goal_weight(target_weight_kg)

    direction = _determine_direction(
        starting_weight_kg=validated_starting,
        target_weight_kg=validated_target,
    )

    return BodyWeightGoal(
        starting_weight_kg=validated_starting,
        target_weight_kg=validated_target,
        direction=direction,
    )


# ---------------------------------------------------------------------------
# Progress calculation
# ---------------------------------------------------------------------------


def calculate_body_weight_goal_progress(
    *,
    starting_weight_kg: Decimal,
    current_weight_kg: Decimal,
    target_weight_kg: Decimal,
) -> BodyWeightGoalProgressResult:
    validated_starting = _validate_goal_weight(starting_weight_kg)
    validated_current = _validate_goal_weight(current_weight_kg)
    validated_target = _validate_goal_weight(target_weight_kg)

    if validated_starting == validated_target:
        raise InvalidBodyWeightGoalProgressError()

    direction = _determine_direction(
        starting_weight_kg=validated_starting,
        target_weight_kg=validated_target,
    )

    total_change_required_kg = abs(validated_target - validated_starting)

    if direction is BodyWeightGoalDirection.DECREASE:
        change_achieved_kg = validated_starting - validated_current
    else:
        change_achieved_kg = validated_current - validated_starting

    remaining_change_kg = total_change_required_kg - change_achieved_kg

    progress_percentage = (
        (change_achieved_kg / total_change_required_kg) * Decimal("100")
    ).quantize(
        BODY_WEIGHT_GOAL_PERCENTAGE_DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    )

    total_change_required_kg = total_change_required_kg.quantize(
        BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP
    )
    change_achieved_kg = change_achieved_kg.quantize(
        BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP
    )
    remaining_change_kg = remaining_change_kg.quantize(
        BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP
    )

    if direction is BodyWeightGoalDirection.DECREASE:
        if validated_current >= validated_starting:
            status = BodyWeightGoalStatus.NOT_STARTED
        elif validated_current > validated_target:
            status = BodyWeightGoalStatus.IN_PROGRESS
        elif validated_current == validated_target:
            status = BodyWeightGoalStatus.TARGET_REACHED
        else:
            status = BodyWeightGoalStatus.TARGET_PASSED
    else:
        if validated_current <= validated_starting:
            status = BodyWeightGoalStatus.NOT_STARTED
        elif validated_current < validated_target:
            status = BodyWeightGoalStatus.IN_PROGRESS
        elif validated_current == validated_target:
            status = BodyWeightGoalStatus.TARGET_REACHED
        else:
            status = BodyWeightGoalStatus.TARGET_PASSED

    return BodyWeightGoalProgressResult(
        starting_weight_kg=validated_starting,
        current_weight_kg=validated_current,
        target_weight_kg=validated_target,
        direction=direction,
        total_change_required_kg=total_change_required_kg,
        change_achieved_kg=change_achieved_kg,
        remaining_change_kg=remaining_change_kg,
        progress_percentage=progress_percentage,
        status=status,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "BODY_WEIGHT_GOAL_PERCENTAGE_DECIMAL_PLACES",
    "BodyWeightGoalDirection",
    "BodyWeightGoalStatus",
    "BodyWeightGoal",
    "BodyWeightGoalProgressResult",
    "create_body_weight_goal",
    "calculate_body_weight_goal_progress",
]
