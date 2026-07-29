from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.body_weight_trends import (
    BodyWeightTrendDirection,
    BodyWeightTrendResult,
)

# ---------------------------------------------------------------------------
# Decimal validation helpers
# ---------------------------------------------------------------------------


def _validate_finite_positive(value: object, field_name: str) -> Decimal:
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
    return d


def _validate_finite(value: object, field_name: str) -> Decimal:
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
# BodyWeightTrendData
# ---------------------------------------------------------------------------


class BodyWeightTrendData(BaseModel):
    observation_count: int
    first_logged_date: date
    latest_logged_date: date
    starting_weight_kg: Decimal
    latest_weight_kg: Decimal
    absolute_change_kg: Decimal
    percentage_change: Decimal
    direction: BodyWeightTrendDirection
    requires_onboarding: bool | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @field_validator("observation_count", mode="before")
    @classmethod
    def validate_observation_count(cls, v: object) -> int:
        if isinstance(v, bool):
            raise ValueError("observation_count must be an integer, not a boolean")
        if not isinstance(v, int):
            raise ValueError("observation_count must be an integer")
        if v < 0:
            raise ValueError("observation_count must be at least 0")
        return v

    @field_validator("starting_weight_kg", mode="before")
    @classmethod
    def validate_starting_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_positive(v, "starting_weight_kg")

    @field_validator("latest_weight_kg", mode="before")
    @classmethod
    def validate_latest_weight_kg(cls, v: object) -> Decimal:
        return _validate_finite_positive(v, "latest_weight_kg")

    @field_validator("absolute_change_kg", mode="before")
    @classmethod
    def validate_absolute_change_kg(cls, v: object) -> Decimal:
        return _validate_finite(v, "absolute_change_kg")

    @field_validator("percentage_change", mode="before")
    @classmethod
    def validate_percentage_change(cls, v: object) -> Decimal:
        return _validate_finite(v, "percentage_change")

    @model_validator(mode="after")
    def _validate_date_order(self) -> BodyWeightTrendData:
        if self.latest_logged_date < self.first_logged_date:
            raise ValueError(
                "latest_logged_date must be greater than or equal to first_logged_date"
            )
        return self

    @classmethod
    def from_result(cls, result: BodyWeightTrendResult) -> BodyWeightTrendData:
        return cls(
            observation_count=result.observation_count,
            first_logged_date=result.first_logged_date,
            latest_logged_date=result.latest_logged_date,
            starting_weight_kg=result.starting_weight_kg,
            latest_weight_kg=result.latest_weight_kg,
            absolute_change_kg=result.absolute_change_kg,
            percentage_change=result.percentage_change,
            direction=result.direction,
        )


# ---------------------------------------------------------------------------
# BodyWeightTrendSuccessResponse
# ---------------------------------------------------------------------------


class BodyWeightTrendSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Body-weight trend calculated successfully."
    data: BodyWeightTrendData

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "BodyWeightTrendData",
    "BodyWeightTrendSuccessResponse",
]
