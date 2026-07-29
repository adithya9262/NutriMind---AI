from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.body_weight import (
    BODY_WEIGHT_DECIMAL_PLACES,
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
)
from app.core.body_weight_goals import (
    BodyWeightGoal,
    BodyWeightGoalDirection,
    BodyWeightGoalProgressResult,
    BodyWeightGoalStatus,
)

# ---------------------------------------------------------------------------
# Decimal validation helpers
# ---------------------------------------------------------------------------


def _validate_goal_weight_input(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    try:
        d = Decimal(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a valid decimal number")
    if not d.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    normalized = d.quantize(BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP)
    if normalized < MIN_BODY_WEIGHT_KG:
        raise ValueError(f"{field_name} must be at least {MIN_BODY_WEIGHT_KG}")
    if normalized > MAX_BODY_WEIGHT_KG:
        raise ValueError(f"{field_name} must be at most {MAX_BODY_WEIGHT_KG}")
    return normalized


def _validate_finite_weight(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    try:
        d = Decimal(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a valid decimal number")
    if not d.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    if d < MIN_BODY_WEIGHT_KG:
        raise ValueError(f"{field_name} must be at least {MIN_BODY_WEIGHT_KG}")
    if d > MAX_BODY_WEIGHT_KG:
        raise ValueError(f"{field_name} must be at most {MAX_BODY_WEIGHT_KG}")
    return d


def _validate_finite_positive_weight(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    try:
        d = Decimal(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a valid decimal number")
    if not d.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    if d <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    if d < MIN_BODY_WEIGHT_KG:
        raise ValueError(f"{field_name} must be at least {MIN_BODY_WEIGHT_KG}")
    if d > MAX_BODY_WEIGHT_KG:
        raise ValueError(f"{field_name} must be at most {MAX_BODY_WEIGHT_KG}")
    return d


def _validate_finite_signed(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    try:
        d = Decimal(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a valid decimal number")
    if not d.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    return d


# ---------------------------------------------------------------------------
# BodyWeightGoalCreate  (input schema)
# ---------------------------------------------------------------------------


class BodyWeightGoalCreate(BaseModel):
    starting_weight_kg: Decimal
    target_weight_kg: Decimal

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @field_validator("starting_weight_kg", "target_weight_kg", mode="before")
    @classmethod
    def validate_weights(cls, v: object, info) -> Decimal:
        field_name = info.field_name or "weight"
        return _validate_goal_weight_input(v, field_name)


# ---------------------------------------------------------------------------
# BodyWeightGoalData  (domain response schema)
# ---------------------------------------------------------------------------


class BodyWeightGoalData(BaseModel):
    starting_weight_kg: Decimal
    target_weight_kg: Decimal
    direction: BodyWeightGoalDirection

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @field_validator("starting_weight_kg", mode="before")
    @classmethod
    def validate_starting_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_weight(v, "starting_weight_kg")

    @field_validator("target_weight_kg", mode="before")
    @classmethod
    def validate_target_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_weight(v, "target_weight_kg")

    @classmethod
    def from_domain(cls, goal: BodyWeightGoal) -> BodyWeightGoalData:
        if not isinstance(goal, BodyWeightGoal):
            raise TypeError("goal must be a BodyWeightGoal instance")
        return cls(
            starting_weight_kg=goal.starting_weight_kg,
            target_weight_kg=goal.target_weight_kg,
            direction=goal.direction,
        )


# ---------------------------------------------------------------------------
# BodyWeightGoalProgressData  (result response schema)
# ---------------------------------------------------------------------------


class BodyWeightGoalProgressData(BaseModel):
    starting_weight_kg: Decimal
    current_weight_kg: Decimal
    target_weight_kg: Decimal
    direction: BodyWeightGoalDirection
    total_change_required_kg: Decimal
    change_achieved_kg: Decimal
    remaining_change_kg: Decimal
    progress_percentage: Decimal
    status: BodyWeightGoalStatus
    requires_onboarding: bool | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @field_validator("starting_weight_kg", mode="before")
    @classmethod
    def validate_starting_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_positive_weight(v, "starting_weight_kg")

    @field_validator("current_weight_kg", mode="before")
    @classmethod
    def validate_current_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_positive_weight(v, "current_weight_kg")

    @field_validator("target_weight_kg", mode="before")
    @classmethod
    def validate_target_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_positive_weight(v, "target_weight_kg")

    @field_validator("total_change_required_kg", mode="before")
    @classmethod
    def validate_total_change_required_kg(cls, v: object) -> Decimal:
        d = _validate_finite_signed(v, "total_change_required_kg")
        if d < Decimal("0"):
            raise ValueError("total_change_required_kg must be non-negative")
        return d

    @field_validator("change_achieved_kg", mode="before")
    @classmethod
    def validate_change_achieved_kg(cls, v: object) -> Decimal:
        return _validate_finite_signed(v, "change_achieved_kg")

    @field_validator("remaining_change_kg", mode="before")
    @classmethod
    def validate_remaining_change_kg(cls, v: object) -> Decimal:
        return _validate_finite_signed(v, "remaining_change_kg")

    @field_validator("progress_percentage", mode="before")
    @classmethod
    def validate_progress_percentage(cls, v: object) -> Decimal:
        return _validate_finite_signed(v, "progress_percentage")

    @classmethod
    def from_result(cls, result: BodyWeightGoalProgressResult) -> BodyWeightGoalProgressData:
        if not isinstance(result, BodyWeightGoalProgressResult):
            raise TypeError("result must be a BodyWeightGoalProgressResult instance")
        return cls(
            starting_weight_kg=result.starting_weight_kg,
            current_weight_kg=result.current_weight_kg,
            target_weight_kg=result.target_weight_kg,
            direction=result.direction,
            total_change_required_kg=result.total_change_required_kg,
            change_achieved_kg=result.change_achieved_kg,
            remaining_change_kg=result.remaining_change_kg,
            progress_percentage=result.progress_percentage,
            status=result.status,
        )


# ---------------------------------------------------------------------------
# Success response schemas
# ---------------------------------------------------------------------------


class BodyWeightGoalSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Body-weight goal created successfully."
    data: BodyWeightGoalData

    model_config = ConfigDict(extra="forbid")


class BodyWeightGoalProgressSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Body-weight goal progress calculated successfully."
    data: BodyWeightGoalProgressData

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "BodyWeightGoalCreate",
    "BodyWeightGoalData",
    "BodyWeightGoalProgressData",
    "BodyWeightGoalSuccessResponse",
    "BodyWeightGoalProgressSuccessResponse",
]
