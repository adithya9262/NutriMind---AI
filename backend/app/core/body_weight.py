from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.core.body_weight_exceptions import (
    DuplicateBodyWeightDateError,
    InvalidBodyWeightError,
)

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

MIN_BODY_WEIGHT_KG: Decimal = Decimal("10.00")
MAX_BODY_WEIGHT_KG: Decimal = Decimal("700.00")
BODY_WEIGHT_DECIMAL_PLACES: Decimal = Decimal("0.01")

# ---------------------------------------------------------------------------
# Body-weight entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BodyWeightEntry:
    entry_id: UUID
    logged_date: date
    weight_kg: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.entry_id, UUID):
            raise InvalidBodyWeightError("entry_id must be a UUID instance")

        if isinstance(self.logged_date, datetime) or not isinstance(self.logged_date, date):
            raise InvalidBodyWeightError("logged_date must be a date instance (not datetime)")

        object.__setattr__(
            self,
            "weight_kg",
            _validate_weight_kg(self.weight_kg),
        )


# ---------------------------------------------------------------------------
# Weight validation
# ---------------------------------------------------------------------------


def _validate_weight_kg(value: object) -> Decimal:
    if isinstance(value, bool):
        raise InvalidBodyWeightError("weight_kg must not be a boolean")

    if isinstance(value, int):
        value = Decimal(str(value))
    elif isinstance(value, Decimal):
        pass
    else:
        raise InvalidBodyWeightError("weight_kg must be a Decimal or integer")

    if not value.is_finite():
        raise InvalidBodyWeightError("weight_kg must be a finite number")

    normalized = value.quantize(BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP)

    if normalized < MIN_BODY_WEIGHT_KG:
        raise InvalidBodyWeightError(f"weight_kg must be at least {MIN_BODY_WEIGHT_KG}")
    if normalized > MAX_BODY_WEIGHT_KG:
        raise InvalidBodyWeightError(f"weight_kg must be at most {MAX_BODY_WEIGHT_KG}")

    return normalized


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


def order_body_weight_entries(
    entries: Iterable[BodyWeightEntry],
) -> tuple[BodyWeightEntry, ...]:
    result = list(entries)
    for item in result:
        if not isinstance(item, BodyWeightEntry):
            raise InvalidBodyWeightError("Each entry must be a BodyWeightEntry instance")
    result.sort(key=lambda e: (e.logged_date, e.entry_id))
    return tuple(result)


# ---------------------------------------------------------------------------
# Duplicate-date detection
# ---------------------------------------------------------------------------


def ensure_unique_body_weight_dates(
    entries: Iterable[BodyWeightEntry],
) -> tuple[BodyWeightEntry, ...]:
    result = list(entries)
    for item in result:
        if not isinstance(item, BodyWeightEntry):
            raise InvalidBodyWeightError("Each entry must be a BodyWeightEntry instance")
    seen: set[date] = set()
    for entry in result:
        if entry.logged_date in seen:
            raise DuplicateBodyWeightDateError(
                "A body-weight entry already exists for the selected date."
            )
        seen.add(entry.logged_date)
    return tuple(result)


# ---------------------------------------------------------------------------
# Combined validation helper
# ---------------------------------------------------------------------------


def validate_body_weight_history(
    entries: Iterable[BodyWeightEntry],
) -> tuple[BodyWeightEntry, ...]:
    materialized = list(entries)
    for item in materialized:
        if not isinstance(item, BodyWeightEntry):
            raise InvalidBodyWeightError("Each entry must be a BodyWeightEntry instance")
    unique = ensure_unique_body_weight_dates(materialized)
    return order_body_weight_entries(unique)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "MIN_BODY_WEIGHT_KG",
    "MAX_BODY_WEIGHT_KG",
    "BODY_WEIGHT_DECIMAL_PLACES",
    "BodyWeightEntry",
    "order_body_weight_entries",
    "ensure_unique_body_weight_dates",
    "validate_body_weight_history",
]
