from __future__ import annotations

import enum
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.core.body_weight import BODY_WEIGHT_DECIMAL_PLACES, BodyWeightEntry
from app.core.body_weight_trend_exceptions import InsufficientBodyWeightHistoryError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES: Decimal = Decimal("0.01")

# ---------------------------------------------------------------------------
# Trend direction
# ---------------------------------------------------------------------------


class BodyWeightTrendDirection(enum.StrEnum):
    DECREASED = "decreased"
    STABLE = "stable"
    INCREASED = "increased"


# ---------------------------------------------------------------------------
# Trend result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BodyWeightTrendResult:
    observation_count: int
    first_logged_date: date
    latest_logged_date: date
    starting_weight_kg: Decimal
    latest_weight_kg: Decimal
    absolute_change_kg: Decimal
    percentage_change: Decimal
    direction: BodyWeightTrendDirection


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


def calculate_body_weight_trend(
    *,
    entries: Iterable[BodyWeightEntry],
) -> BodyWeightTrendResult:
    materialized = list(entries)

    if len(materialized) < 2:
        raise InsufficientBodyWeightHistoryError()

    sorted_entries = sorted(materialized, key=lambda e: (e.logged_date, e.entry_id))

    first = sorted_entries[0]
    last = sorted_entries[-1]

    starting_weight_kg = first.weight_kg
    latest_weight_kg = last.weight_kg

    absolute_change_kg = (latest_weight_kg - starting_weight_kg).quantize(
        BODY_WEIGHT_DECIMAL_PLACES, rounding=ROUND_HALF_UP
    )

    percentage_change = (
        ((latest_weight_kg - starting_weight_kg) / starting_weight_kg) * Decimal("100")
    ).quantize(BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES, rounding=ROUND_HALF_UP)

    raw_change = latest_weight_kg - starting_weight_kg
    if raw_change < Decimal("0"):
        direction = BodyWeightTrendDirection.DECREASED
    elif raw_change == Decimal("0"):
        direction = BodyWeightTrendDirection.STABLE
    else:
        direction = BodyWeightTrendDirection.INCREASED

    return BodyWeightTrendResult(
        observation_count=len(sorted_entries),
        first_logged_date=first.logged_date,
        latest_logged_date=last.logged_date,
        starting_weight_kg=starting_weight_kg,
        latest_weight_kg=latest_weight_kg,
        absolute_change_kg=absolute_change_kg,
        percentage_change=percentage_change,
        direction=direction,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES",
    "BodyWeightTrendDirection",
    "BodyWeightTrendResult",
    "calculate_body_weight_trend",
]
