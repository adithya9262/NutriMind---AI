from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.body_weight import (
    BODY_WEIGHT_DECIMAL_PLACES,
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
    BodyWeightEntry,
)

# ---------------------------------------------------------------------------
# Decimal validation helper
# ---------------------------------------------------------------------------


def _validate_weight_kg(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("weight_kg must not be a boolean")
    try:
        d = Decimal(str(value))
    except Exception:
        raise ValueError("weight_kg must be a valid decimal number")
    if not d.is_finite():
        raise ValueError("weight_kg must be a finite number")
    normalized = d.quantize(BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP)
    if normalized < MIN_BODY_WEIGHT_KG:
        raise ValueError(f"weight_kg must be at least {MIN_BODY_WEIGHT_KG}")
    if normalized > MAX_BODY_WEIGHT_KG:
        raise ValueError(f"weight_kg must be at most {MAX_BODY_WEIGHT_KG}")
    return normalized


# ---------------------------------------------------------------------------
# BodyWeightEntryCreate  (input schema)
# ---------------------------------------------------------------------------


class BodyWeightEntryCreate(BaseModel):
    weight_kg: Decimal

    model_config = ConfigDict(extra="forbid")

    @field_validator("weight_kg", mode="before")
    @classmethod
    def validate_weight_kg(cls, v: object) -> Decimal:
        if isinstance(v, (int, float)):
            v = str(v)
        return _validate_weight_kg(v)


# ---------------------------------------------------------------------------
# BodyWeightEntryData  (public response schema)
# ---------------------------------------------------------------------------


class BodyWeightEntryData(BaseModel):
    entry_id: UUID
    logged_date: date
    weight_kg: Decimal

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        from_attributes=True,
    )

    @field_validator("weight_kg", mode="before")
    @classmethod
    def validate_weight_kg(cls, v: object) -> Decimal:
        if isinstance(v, (int, float)):
            v = str(v)
        return _validate_weight_kg(v)

    @classmethod
    def from_domain(cls, entry: BodyWeightEntry) -> BodyWeightEntryData:
        if not isinstance(entry, BodyWeightEntry):
            raise TypeError("entry must be a BodyWeightEntry")
        return cls(
            entry_id=entry.entry_id,
            logged_date=entry.logged_date,
            weight_kg=entry.weight_kg,
        )


# ---------------------------------------------------------------------------
# BodyWeightHistoryData  (collection response schema)
# ---------------------------------------------------------------------------


class BodyWeightHistoryData(BaseModel):
    entries: tuple[BodyWeightEntryData, ...]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @model_validator(mode="after")
    def _validate_unique(self) -> BodyWeightHistoryData:
        seen_dates: set[date] = set()
        seen_ids: set[UUID] = set()
        for entry in self.entries:
            if entry.logged_date in seen_dates:
                raise ValueError(
                    f"Duplicate logged_date in body-weight history: {entry.logged_date.isoformat()}"
                )
            seen_dates.add(entry.logged_date)
            if entry.entry_id in seen_ids:
                raise ValueError(f"Duplicate entry_id in body-weight history: {entry.entry_id}")
            seen_ids.add(entry.entry_id)
        return self

    @classmethod
    def from_domain(
        cls,
        entries: Iterable[BodyWeightEntry],
    ) -> BodyWeightHistoryData:
        materialized = tuple(BodyWeightEntryData.from_domain(entry) for entry in entries)
        return cls(entries=materialized)


# ---------------------------------------------------------------------------
# Success response schemas
# ---------------------------------------------------------------------------


class BodyWeightEntrySuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Body-weight entry processed successfully."
    data: BodyWeightEntryData

    model_config = ConfigDict(extra="forbid")


class BodyWeightHistorySuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Body-weight history retrieved successfully."
    data: BodyWeightHistoryData

    model_config = ConfigDict(extra="forbid")


class BodyWeightDeleteSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Body-weight entry deleted successfully."

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "BodyWeightDeleteSuccessResponse",
    "BodyWeightEntryCreate",
    "BodyWeightEntryData",
    "BodyWeightHistoryData",
    "BodyWeightEntrySuccessResponse",
    "BodyWeightHistorySuccessResponse",
]
