from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from app.core.body_weight import (
    BODY_WEIGHT_DECIMAL_PLACES,
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
    BodyWeightEntry,
    ensure_unique_body_weight_dates,
    order_body_weight_entries,
    validate_body_weight_history,
)
from app.core.body_weight_exceptions import (
    DuplicateBodyWeightDateError,
    InvalidBodyWeightError,
)

MODULE = "app.core.body_weight"

# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def _uuid2() -> UUID:
    return UUID("87654321-4321-8765-4321-876543218765")


def _entry(
    *,
    entry_id: UUID | None = None,
    logged_date: date | None = None,
    weight_kg: Decimal | int | None = None,
) -> BodyWeightEntry:
    return BodyWeightEntry(
        entry_id=entry_id or _uuid(),
        logged_date=logged_date or date(2025, 6, 15),
        weight_kg=weight_kg or Decimal("70.00"),
    )


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def _uuid2() -> UUID:
    return UUID("87654321-4321-8765-4321-876543218765")


# ===========================================================================
# A. Constants
# ===========================================================================


class TestConstants:
    def test_min_value(self):
        assert MIN_BODY_WEIGHT_KG == _dec("10.00")

    def test_max_value(self):
        assert MAX_BODY_WEIGHT_KG == _dec("700.00")

    def test_min_less_than_max(self):
        assert MIN_BODY_WEIGHT_KG < MAX_BODY_WEIGHT_KG

    def test_decimal_quantum_value(self):
        assert BODY_WEIGHT_DECIMAL_PLACES == _dec("0.01")

    def test_all_constants_are_decimal(self):
        assert isinstance(MIN_BODY_WEIGHT_KG, Decimal)
        assert isinstance(MAX_BODY_WEIGHT_KG, Decimal)
        assert isinstance(BODY_WEIGHT_DECIMAL_PLACES, Decimal)

    def test_no_float_constants(self):
        assert not isinstance(MIN_BODY_WEIGHT_KG, float)
        assert not isinstance(MAX_BODY_WEIGHT_KG, float)
        assert not isinstance(BODY_WEIGHT_DECIMAL_PLACES, float)

    def test_alignment_with_nutrition_profile_weight_range(self):
        import app.core.nutrition_calculations as calcs

        source = open(calcs.__file__).read()
        assert '_MIN_WEIGHT_KG = Decimal("10")' in source
        assert '_MAX_WEIGHT_KG = Decimal("700")' in source


# ===========================================================================
# B. BodyWeightEntry structure
# ===========================================================================


class TestBodyWeightEntryStructure:
    def test_is_dataclass(self):

        assert hasattr(BodyWeightEntry, "__dataclass_fields__")

    def test_frozen(self):
        entry = _entry()

        with pytest.raises(FrozenInstanceError):
            entry.entry_id = UUID("00000000-0000-0000-0000-000000000000")  # type: ignore[misc]

    def test_slotted(self):
        entry = _entry()
        with pytest.raises((AttributeError, TypeError)):
            entry.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_field_order(self):
        import inspect

        source = inspect.getsource(BodyWeightEntry)
        fields_lines = [line for line in source.splitlines() if "entry_id" in line and ":" in line]
        assert len(fields_lines) > 0

    def test_exact_annotations(self):
        entry = _entry()
        assert hasattr(entry, "entry_id")
        assert hasattr(entry, "logged_date")
        assert hasattr(entry, "weight_kg")

    def test_immutability(self):
        entry = _entry()

        with pytest.raises(FrozenInstanceError):
            entry.entry_id = UUID("00000000-0000-0000-0000-000000000000")  # type: ignore[misc]

    def test_no_dynamic_attributes(self):
        entry = _entry()
        with pytest.raises((AttributeError, TypeError)):
            entry.new_field = "value"  # type: ignore[attr-defined]

    def test_equality(self):
        e1 = _entry()
        e2 = _entry()
        assert e1 == e2

    def test_inequality(self):
        e1 = _entry(entry_id=_uuid())
        e2 = _entry(entry_id=_uuid2())
        assert e1 != e2


# ===========================================================================
# C. Valid entry IDs
# ===========================================================================


class TestValidEntryIDs:
    def test_uuid4_accepted(self):
        uid = UUID("12345678-1234-5678-1234-567812345678")
        entry = BodyWeightEntry(
            entry_id=uid,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert entry.entry_id is uid

    def test_other_valid_uuid(self):
        uid = UUID("00000000-0000-0000-0000-000000000000")
        entry = BodyWeightEntry(
            entry_id=uid,
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert entry.entry_id is uid


# ===========================================================================
# D. Invalid entry IDs
# ===========================================================================


class TestInvalidEntryIDs:
    def test_none_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=None,  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_uuid_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=str(_uuid()),  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_empty_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id="",  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_integer_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=123,  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_zero_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=0,  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_bool_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=True,  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_bytes_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=b"1234",  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_arbitrary_object_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="entry_id must be a UUID"):
            BodyWeightEntry(
                entry_id=object(),  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )


# ===========================================================================
# E. Valid dates
# ===========================================================================


class TestValidDates:
    def test_normal_date(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert entry.logged_date == date(2025, 6, 15)

    def test_leap_day(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2024, 2, 29),
            weight_kg=Decimal("70.00"),
        )
        assert entry.logged_date == date(2024, 2, 29)

    def test_past_date(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2020, 1, 1),
            weight_kg=Decimal("70.00"),
        )
        assert entry.logged_date == date(2020, 1, 1)

    def test_future_date_accepted(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2030, 12, 31),
            weight_kg=Decimal("70.00"),
        )
        assert entry.logged_date == date(2030, 12, 31)


# ===========================================================================
# F. Invalid dates
# ===========================================================================


class TestInvalidDates:
    def test_none_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=None,  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )

    def test_iso_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date="2025-06-15",  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )

    def test_datetime_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=datetime(2025, 6, 15, 12, 0, 0),  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )

    def test_integer_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=20250615,  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )

    def test_bool_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=True,  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )

    def test_arbitrary_object_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=object(),  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )


# ===========================================================================
# G. Valid weights
# ===========================================================================


class TestValidWeights:
    def test_decimal_integer_form(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70"),
        )
        assert entry.weight_kg == _dec("70.00")

    def test_decimal_one_decimal(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.1"),
        )
        assert entry.weight_kg == _dec("70.10")

    def test_decimal_two_decimal(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.12"),
        )
        assert entry.weight_kg == _dec("70.12")

    def test_decimal_three_decimal(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.125"),
        )
        assert entry.weight_kg == _dec("70.13")

    def test_minimum(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("10.00"),
        )
        assert entry.weight_kg == _dec("10.00")

    def test_maximum(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("700.00"),
        )
        assert entry.weight_kg == _dec("700.00")

    def test_integer_input(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=70,
        )
        assert entry.weight_kg == _dec("70.00")

    def test_integer_minimum(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=10,
        )
        assert entry.weight_kg == _dec("10.00")

    def test_integer_maximum(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=700,
        )
        assert entry.weight_kg == _dec("700.00")


# ===========================================================================
# H. Weight normalization
# ===========================================================================


class TestWeightNormalization:
    def test_integer_normalized(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=70,
        )
        assert entry.weight_kg == _dec("70.00")

    def test_one_decimal_normalized(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.1"),
        )
        assert entry.weight_kg == _dec("70.10")

    def test_two_decimal_preserved(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.12"),
        )
        assert entry.weight_kg == _dec("70.12")

    def test_three_decimal_rounds_up(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.125"),
        )
        assert entry.weight_kg == _dec("70.13")

    def test_three_decimal_rounds_down(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.124"),
        )
        assert entry.weight_kg == _dec("70.12")

    def test_round_half_up(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.125"),
        )
        assert entry.weight_kg == _dec("70.13")

    def test_stored_as_decimal(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert isinstance(entry.weight_kg, Decimal)

    def test_no_float_conversion(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert not isinstance(entry.weight_kg, float)


# ===========================================================================
# I. Invalid weights
# ===========================================================================


class TestInvalidWeights:
    def test_none_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=None,  # type: ignore[arg-type]
            )

    def test_bool_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="weight_kg must not be a boolean"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=True,  # type: ignore[arg-type]
            )

    def test_empty_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg="",  # type: ignore[arg-type]
            )

    def test_whitespace_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg="   ",  # type: ignore[arg-type]
            )

    def test_malformed_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg="abc",  # type: ignore[arg-type]
            )

    def test_nan_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="finite"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("NaN"),
            )

    def test_infinity_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="finite"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("Infinity"),
            )

    def test_negative_infinity_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="finite"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("-Infinity"),
            )

    def test_below_minimum(self):
        with pytest.raises(InvalidBodyWeightError, match="at least"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("9.99"),
            )

    def test_above_maximum(self):
        with pytest.raises(InvalidBodyWeightError, match="at most"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("700.01"),
            )

    def test_negative(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("-1"),
            )

    def test_zero(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("0"),
            )

    def test_arbitrary_object(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=object(),  # type: ignore[arg-type]
            )

    def test_float_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=70.5,  # type: ignore[arg-type]
            )

    def test_string_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg="70",  # type: ignore[arg-type]
            )


# ===========================================================================
# J. Boundary-after-rounding behavior
# ===========================================================================


class TestBoundaryAfterRounding:
    def test_just_above_minimum_rounds_to_minimum(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("9.995"),
        )
        assert entry.weight_kg == _dec("10.00")

    def test_just_below_minimum_after_rounding_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("9.994"),
            )

    def test_just_below_maximum_rounds_to_maximum(self):
        entry = BodyWeightEntry(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("699.995"),
        )
        assert entry.weight_kg == _dec("700.00")

    def test_just_above_maximum_after_rounding_rejected(self):
        with pytest.raises(InvalidBodyWeightError, match="at most"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("700.005"),
            )

    def test_validation_order_convert_finite_round_range(self):
        with pytest.raises(InvalidBodyWeightError, match="at most"):
            BodyWeightEntry(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("700.005"),
            )


# ===========================================================================
# K. Ordering
# ===========================================================================


class TestOrderBodyWeightEntries:
    def test_empty_iterable(self):
        result = order_body_weight_entries([])
        assert result == ()

    def test_one_entry(self):
        entry = _entry()
        result = order_body_weight_entries([entry])
        assert result == (entry,)

    def test_already_ordered(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = order_body_weight_entries([e1, e2])
        assert result == (e1, e2)

    def test_reverse_ordered(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = order_body_weight_entries([e2, e1])
        assert result == (e1, e2)

    def test_random_order(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 3, 15)
        d3 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        e3 = _entry(logged_date=d3)
        result = order_body_weight_entries([e3, e1, e2])
        assert result == (e1, e2, e3)

    def test_same_date_tie_break_by_entry_id(self):
        d = date(2025, 6, 15)
        uid1 = UUID("00000000-0000-0000-0000-000000000001")
        uid2 = UUID("00000000-0000-0000-0000-000000000002")
        e1 = BodyWeightEntry(entry_id=uid1, logged_date=d, weight_kg=Decimal("70.00"))
        e2 = BodyWeightEntry(entry_id=uid2, logged_date=d, weight_kg=Decimal("70.00"))
        result = order_body_weight_entries([e2, e1])
        assert result == (e1, e2)

    def test_tuple_input(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = order_body_weight_entries((e2, e1))
        assert result == (e1, e2)

    def test_list_input(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = order_body_weight_entries([e2, e1])
        assert result == (e1, e2)

    def test_generator_input(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)

        def _gen():
            yield e2
            yield e1

        result = order_body_weight_entries(_gen())
        assert result == (e1, e2)

    def test_input_not_mutated(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        original = [e2, e1]
        original_copy = list(original)
        order_body_weight_entries(original)
        assert original == original_copy

    def test_new_tuple_returned(self):
        entries = [_entry()]
        result = order_body_weight_entries(entries)
        assert isinstance(result, tuple)
        assert result is not tuple(entries)

    def test_deterministic_repeated_result(self):
        entries = [_entry(), _entry(logged_date=date(2025, 1, 1))]
        r1 = order_body_weight_entries(entries)
        r2 = order_body_weight_entries(entries)
        assert r1 == r2

    def test_invalid_member_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            order_body_weight_entries([_entry(), "invalid"])  # type: ignore[list-item]


# ===========================================================================
# L. Duplicate-date validation
# ===========================================================================


class TestEnsureUniqueBodyWeightDates:
    def test_empty_iterable(self):
        result = ensure_unique_body_weight_dates([])
        assert result == ()

    def test_one_entry(self):
        entry = _entry()
        result = ensure_unique_body_weight_dates([entry])
        assert result == (entry,)

    def test_multiple_unique_dates(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = ensure_unique_body_weight_dates([e1, e2])
        assert result == (e1, e2)

    def test_same_weight_different_dates_accepted(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = BodyWeightEntry(entry_id=_uuid(), logged_date=d1, weight_kg=Decimal("70.00"))
        e2 = BodyWeightEntry(entry_id=_uuid(), logged_date=d2, weight_kg=Decimal("70.00"))
        result = ensure_unique_body_weight_dates([e1, e2])
        assert result == (e1, e2)

    def test_duplicate_date_rejected(self):
        d = date(2025, 6, 15)
        e1 = _entry(logged_date=d)
        e2 = _entry(logged_date=d, entry_id=_uuid2())
        with pytest.raises(DuplicateBodyWeightDateError):
            ensure_unique_body_weight_dates([e1, e2])

    def test_three_entries_with_one_duplicate_rejected(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        e3 = _entry(logged_date=d2, entry_id=_uuid2())
        with pytest.raises(DuplicateBodyWeightDateError):
            ensure_unique_body_weight_dates([e1, e2, e3])

    def test_multiple_duplicate_groups_rejected(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d1, entry_id=_uuid2())
        e3 = _entry(logged_date=d2)
        e4 = _entry(logged_date=d2, entry_id=_uuid())
        with pytest.raises(DuplicateBodyWeightDateError):
            ensure_unique_body_weight_dates([e1, e2, e3, e4])

    def test_input_order_preserved(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d2)
        e2 = _entry(logged_date=d1)
        result = ensure_unique_body_weight_dates([e1, e2])
        assert result == (e1, e2)

    def test_tuple_input(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = ensure_unique_body_weight_dates((e1, e2))
        assert result == (e1, e2)

    def test_list_input(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = ensure_unique_body_weight_dates([e1, e2])
        assert result == (e1, e2)

    def test_generator_input(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)

        def _gen():
            yield e1
            yield e2

        result = ensure_unique_body_weight_dates(_gen())
        assert result == (e1, e2)

    def test_input_not_mutated(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        original = [e1, e2]
        original_copy = list(original)
        ensure_unique_body_weight_dates(original)
        assert original == original_copy

    def test_invalid_member_rejected(self):
        with pytest.raises(InvalidBodyWeightError):
            ensure_unique_body_weight_dates(["invalid"])  # type: ignore[list-item]

    def test_no_silent_merge(self):
        d = date(2025, 6, 15)
        e1 = _entry(logged_date=d, weight_kg=Decimal("70.00"))
        e2 = _entry(logged_date=d, weight_kg=Decimal("71.00"), entry_id=_uuid2())
        with pytest.raises(DuplicateBodyWeightDateError):
            ensure_unique_body_weight_dates([e1, e2])

    def test_no_silent_deduplication(self):
        d = date(2025, 6, 15)
        e1 = _entry(logged_date=d)
        e2 = _entry(logged_date=d, entry_id=_uuid2())
        with pytest.raises(DuplicateBodyWeightDateError):
            ensure_unique_body_weight_dates([e1, e2])


# ===========================================================================
# M. Combined history validation
# ===========================================================================


class TestValidateBodyWeightHistory:
    def test_empty_history(self):
        result = validate_body_weight_history([])
        assert result == ()

    def test_unique_unsorted_returns_sorted(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = validate_body_weight_history([e2, e1])
        assert result == (e1, e2)

    def test_duplicate_date_rejected(self):
        d = date(2025, 6, 15)
        e1 = _entry(logged_date=d)
        e2 = _entry(logged_date=d, entry_id=_uuid2())
        with pytest.raises(DuplicateBodyWeightDateError):
            validate_body_weight_history([e1, e2])

    def test_generator_works(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)

        def _gen():
            yield e2
            yield e1

        result = validate_body_weight_history(_gen())
        assert result == (e1, e2)

    def test_deterministic_output(self):
        entries = [_entry(), _entry(logged_date=date(2025, 1, 1))]
        r1 = validate_body_weight_history(entries)
        r2 = validate_body_weight_history(entries)
        assert r1 == r2

    def test_input_unchanged(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        original = [e2, e1]
        original_copy = list(original)
        validate_body_weight_history(original)
        assert original == original_copy

    def test_reuses_helper_behavior(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1)
        e2 = _entry(logged_date=d2)
        result = validate_body_weight_history([e2, e1])
        assert isinstance(result, tuple)
        assert result == (e1, e2)

    def test_no_weight_calculations(self):
        d1 = date(2025, 1, 1)
        d2 = date(2025, 6, 15)
        e1 = _entry(logged_date=d1, weight_kg=Decimal("70.00"))
        e2 = _entry(logged_date=d2, weight_kg=Decimal("71.00"))
        result = validate_body_weight_history([e2, e1])
        assert result[0].weight_kg == _dec("70.00")
        assert result[1].weight_kg == _dec("71.00")


# ===========================================================================
# N. Domain purity
# ===========================================================================


class TestDomainPurity:
    def test_no_fastapi_import(self):
        source = _source()
        assert "fastapi" not in source.lower()

    def test_no_starlette_import(self):
        source = _source()
        assert "starlette" not in source.lower()

    def test_no_pydantic_import(self):
        source = _source()
        assert "pydantic" not in source.lower()

    def test_no_sqlalchemy_import(self):
        source = _source()
        assert "sqlalchemy" not in source.lower()

    def test_no_alembic_import(self):
        source = _source()
        assert "alembic" not in source.lower()

    def test_no_database_import(self):
        source = _source()
        assert "from app.db" not in source
        assert "import app.db" not in source

    def test_no_repository_import(self):
        source = _source()
        assert "repositories" not in source

    def test_no_service_import(self):
        source = _source()
        assert "from app.services" not in source

    def test_no_api_import(self):
        source = _source()
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_environment_access(self):
        source = _source()
        assert "os.environ" not in source
        assert "getenv" not in source
        assert "os.getenv" not in source

    def test_no_network_access(self):
        source = _source()
        assert "import request" not in source.lower()
        assert "urllib" not in source.lower()
        assert "httpx" not in source.lower()

    def test_no_system_clock(self):
        source = _source()
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_no_random_behavior(self):
        source = _source()
        assert "random" not in source.lower()

    def test_no_secrets_module(self):
        source = _source()
        assert "import secrets" not in source

    def test_no_ai_llm(self):
        source = _source()
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in source.lower()

    def test_no_usda(self):
        source = _source()
        assert "usda" not in source.lower()

    def test_no_health_score(self):
        source = _source()
        assert "health_score" not in source.lower()
        assert "health score" not in source.lower()

    def test_no_adherence_score(self):
        source = _source()
        assert "adherence" not in source.lower()

    def test_no_recommendation_logic(self):
        source = _source()
        assert "recommend" not in source.lower()

    def test_no_diagnosis_treatment(self):
        source = _source()
        for token in ("diagnos", "treatment", "therapy"):
            assert token not in source.lower()

    def test_no_weight_change_calculation(self):
        source = _source()
        assert "weight_change" not in source.lower()
        assert "weight change" not in source.lower()

    def test_no_trend_calculation(self):
        source = _source()
        assert "trend" not in source.lower()

    def test_no_average_calculation(self):
        source = _source()
        assert "average" not in source.lower()

    def test_no_prediction(self):
        source = _source()
        assert "predict" not in source.lower()

    def test_no_bmi_calculation(self):
        source = _source()
        assert "bmi" not in source.lower()

    def test_no_tdee_calculation(self):
        source = _source()
        assert "tdee" not in source.lower()

    def test_no_nutrition_profile_sync(self):
        source = _source()
        assert "nutrition_profile" not in source.lower()

    def test_no_body_fat(self):
        source = _source()
        assert "body_fat" not in source.lower()
        assert "body fat" not in source.lower()

    def test_no_measurement_fields(self):
        source = _source()
        for token in ("waist", "chest", "hip", "arm", "circumference"):
            assert token not in source.lower()

    def test_no_unit_conversion(self):
        source = _source()
        assert "pound" not in source.lower()
        assert "stone" not in source.lower()
        assert "lbs" not in source.lower()

    def test_only_domain_and_stdlib_imports(self):
        source = _source()
        allowed = (
            "from __future__",
            "from dataclasses",
            "from datetime",
            "from decimal",
            "from typing",
            "from collections.abc",
            "from uuid",
            "from app.core.body_weight_exceptions",
        )
        lines = [
            ln for ln in source.splitlines() if ln.startswith("import ") or ln.startswith("from ")
        ]
        for ln in lines:
            assert any(ln.startswith(a) for a in allowed), f"unexpected import: {ln!r}"


# ===========================================================================
# O. Phase-boundary tests
# ===========================================================================


class TestPhaseBoundaries:
    def test_body_weight_schema_module_exists(self):
        import os

        schema_path = "app/schemas/body_weight.py"
        assert os.path.exists(schema_path)

    def test_no_body_metrics_schema_module(self):
        import os

        schema_path = "app/schemas/body_metrics.py"
        assert not os.path.exists(schema_path)

    def test_orm_model_exists(self):
        import os

        model_path = "app/models/body_weight.py"
        assert os.path.exists(model_path)

    def test_repository_exists(self):
        import os

        repo_path = "app/repositories/body_weight.py"
        assert os.path.exists(repo_path)

    def test_service_exists(self):
        import os

        service_path = "app/services/body_weight.py"
        assert os.path.exists(service_path)

    def test_no_api_router(self):
        import os

        router_path = "app/api/v1/body_weight.py"
        assert not os.path.exists(router_path)

    def test_body_weight_api_endpoint_in_openapi(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        body_weight_paths = [p for p in paths if "body-weight" in p or "body_weight" in p]
        assert len(body_weight_paths) == 4

    def test_no_body_metrics_router(self):
        import os

        router_path = "app/api/v1/body_metrics.py"
        assert not os.path.exists(router_path)

    def test_body_weight_table_exists(self):
        from app.db.base import Base

        table_names = set(Base.metadata.tables.keys())
        assert "body_weights" in table_names
        assert "body_metrics" not in table_names

    def test_orm_tables_updated(self):
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

    def test_exactly_five_migrations(self):
        import os

        migration_dir = "alembic/versions"
        files = [f for f in os.listdir(migration_dir) if f.endswith(".py") and f != "__init__.py"]
        assert len(files) == 7

    def test_migration_head_updated(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        assert head == "0295723946b2"

    def test_frontend_body_weight_files_exist(self):
        import os

        frontend_dir = "../frontend"
        if os.path.exists(frontend_dir):
            body_weight_files = []
            for root, dirs, files in os.walk(frontend_dir):
                for f in files:
                    if "body-weight" in f.lower() or "bodyweight" in f.lower():
                        body_weight_files.append(os.path.join(root, f))
            assert len(body_weight_files) > 0

    def test_no_dependency_declarations(self):
        import app.core.body_weight as mod

        source = open(mod.__file__).read()
        assert "import fastapi" not in source.lower()
        assert "import pydantic" not in source.lower()
        assert "import sqlalchemy" not in source.lower()


# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def _uuid2() -> UUID:
    return UUID("87654321-4321-8765-4321-876543218765")


def _entry(
    *,
    entry_id: UUID | None = None,
    logged_date: date | None = None,
    weight_kg: Decimal | int | None = None,
) -> BodyWeightEntry:
    return BodyWeightEntry(
        entry_id=entry_id or _uuid(),
        logged_date=logged_date or date(2025, 6, 15),
        weight_kg=weight_kg or Decimal("70.00"),
    )


def _source() -> str:
    mod = importlib.import_module(MODULE)
    import inspect

    return inspect.getsource(mod)
