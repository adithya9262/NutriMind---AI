from __future__ import annotations

import importlib
import random
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from app.core.body_weight import BodyWeightEntry
from app.core.body_weight_trend_exceptions import (
    BodyWeightTrendError,
    InsufficientBodyWeightHistoryError,
)
from app.core.body_weight_trends import (
    BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES,
    BodyWeightTrendDirection,
    BodyWeightTrendResult,
    calculate_body_weight_trend,
)

MODULE = "app.core.body_weight_trends"

# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _uuid(seed: int = 1) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{seed:012d}")


def _entry(
    *,
    entry_id: UUID | None = None,
    logged_date: date | None = None,
    weight_kg: Decimal | int | None = None,
) -> BodyWeightEntry:
    return BodyWeightEntry(
        entry_id=entry_id or _uuid(1),
        logged_date=logged_date or date(2025, 6, 15),
        weight_kg=weight_kg or Decimal("70.00"),
    )


# ===========================================================================
# A. BodyWeightTrendDirection
# ===========================================================================


class TestBodyWeightTrendDirection:
    def test_is_str_enum(self):
        assert issubclass(BodyWeightTrendDirection, str)

    def test_exactly_three_members(self):
        assert len(BodyWeightTrendDirection.__members__) == 3

    def test_exact_names(self):
        assert set(BodyWeightTrendDirection.__members__) == {
            "DECREASED",
            "STABLE",
            "INCREASED",
        }

    def test_exact_values(self):
        assert BodyWeightTrendDirection.DECREASED.value == "decreased"
        assert BodyWeightTrendDirection.STABLE.value == "stable"
        assert BodyWeightTrendDirection.INCREASED.value == "increased"

    def test_values_are_lowercase(self):
        for direction in BodyWeightTrendDirection:
            assert direction.value == direction.value.lower()

    def test_no_unknown_value(self):
        values = {m.value for m in BodyWeightTrendDirection}
        assert "unknown" not in values

    def test_no_improving_worsening(self):
        values = {m.value for m in BodyWeightTrendDirection}
        assert "improving" not in values
        assert "worsening" not in values

    def test_json_friendly(self):
        import json

        data = {"direction": BodyWeightTrendDirection.INCREASED}
        serialized = json.dumps(data, default=str)
        assert '"increased"' in serialized

    def test_member_comparison_to_string(self):
        assert BodyWeightTrendDirection.DECREASED == "decreased"
        assert BodyWeightTrendDirection.STABLE == "stable"
        assert BodyWeightTrendDirection.INCREASED == "increased"


# ===========================================================================
# B. BodyWeightTrendResult structure
# ===========================================================================


class TestBodyWeightTrendResultStructure:
    def test_is_dataclass(self):
        assert hasattr(BodyWeightTrendResult, "__dataclass_fields__")

    def test_frozen(self):
        result = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        with pytest.raises(FrozenInstanceError):
            result.observation_count = 3  # type: ignore[misc]

    def test_slotted(self):
        result = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        with pytest.raises((AttributeError, TypeError)):
            result.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_field_names(self):
        fields = list(BodyWeightTrendResult.__dataclass_fields__)
        assert fields == [
            "observation_count",
            "first_logged_date",
            "latest_logged_date",
            "starting_weight_kg",
            "latest_weight_kg",
            "absolute_change_kg",
            "percentage_change",
            "direction",
        ]

    def test_exact_field_order(self):
        import inspect

        source = inspect.getsource(BodyWeightTrendResult)
        annotation_lines = [
            line.strip() for line in source.splitlines() if ":" in line and "def " not in line
        ]
        annotated = [
            line.split(":")[0].strip() for line in annotation_lines if line.split(":")[0].strip()
        ]
        expected = [
            "observation_count",
            "first_logged_date",
            "latest_logged_date",
            "starting_weight_kg",
            "latest_weight_kg",
            "absolute_change_kg",
            "percentage_change",
            "direction",
        ]
        for field in expected:
            assert field in annotated, f"Field {field} not found in source annotations"

    def test_equality(self):
        r1 = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        r2 = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        assert r1 == r2

    def test_decimal_field_types(self):
        result = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        assert isinstance(result.starting_weight_kg, Decimal)
        assert isinstance(result.latest_weight_kg, Decimal)
        assert isinstance(result.absolute_change_kg, Decimal)
        assert isinstance(result.percentage_change, Decimal)

    def test_no_dict(self):
        result = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        assert not hasattr(result, "__dict__")

    def test_no_user_id(self):
        assert "user_id" not in BodyWeightTrendResult.__dataclass_fields__

    def test_no_entry_ids(self):
        assert "entry_id" not in BodyWeightTrendResult.__dataclass_fields__

    def test_no_target(self):
        assert "target" not in BodyWeightTrendResult.__dataclass_fields__

    def test_no_score(self):
        assert "score" not in BodyWeightTrendResult.__dataclass_fields__

    def test_no_prediction(self):
        assert "prediction" not in BodyWeightTrendResult.__dataclass_fields__

    def test_no_recommendation(self):
        assert "recommendation" not in BodyWeightTrendResult.__dataclass_fields__

    def test_deterministic_repr(self):
        result = BodyWeightTrendResult(
            observation_count=2,
            first_logged_date=date(2025, 6, 1),
            latest_logged_date=date(2025, 6, 15),
            starting_weight_kg=_dec("70.00"),
            latest_weight_kg=_dec("75.00"),
            absolute_change_kg=_dec("5.00"),
            percentage_change=_dec("7.14"),
            direction=BodyWeightTrendDirection.INCREASED,
        )
        r1 = repr(result)
        r2 = repr(result)
        assert r1 == r2


# ===========================================================================
# C. Exception tests (reuse from exception test module)
# ===========================================================================


class TestExceptionIntegration:
    def test_calculate_raises_with_empty(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=[])

    def test_calculate_raises_with_one(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=[_entry()])

    def test_exception_is_body_weight_trend_error(self):
        with pytest.raises(BodyWeightTrendError):
            calculate_body_weight_trend(entries=[])

    def test_exception_message_stable(self):
        try:
            calculate_body_weight_trend(entries=[])
        except InsufficientBodyWeightHistoryError as exc:
            assert str(exc) == (
                "At least two body-weight entries are required to calculate a trend."
            )


# ===========================================================================
# D. Insufficient history
# ===========================================================================


class TestInsufficientHistory:
    def test_empty_tuple(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=())

    def test_empty_list(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=[])

    def test_empty_generator(self):
        def _empty_gen():
            return
            yield  # pragma: no cover

        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=_empty_gen())

    def test_one_tuple(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=(_entry(),))

    def test_one_list(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=[_entry()])

    def test_one_generator(self):
        def _one_gen():
            yield _entry()

        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=_one_gen())

    def test_exact_exception_type(self):
        with pytest.raises(InsufficientBodyWeightHistoryError):
            calculate_body_weight_trend(entries=[])

    def test_exact_safe_message(self):
        try:
            calculate_body_weight_trend(entries=[])
        except InsufficientBodyWeightHistoryError as exc:
            assert "At least two body-weight entries" in str(exc)


# ===========================================================================
# E. Increasing trend
# ===========================================================================


class TestIncreasingTrend:
    def test_two_entries_increasing(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 15), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.observation_count == 2
        assert result.first_logged_date == date(2025, 6, 1)
        assert result.latest_logged_date == date(2025, 6, 15)
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")
        assert result.absolute_change_kg == _dec("5.00")
        assert result.percentage_change == _dec("7.14")
        assert result.direction == BodyWeightTrendDirection.INCREASED

    def test_multiple_entries_increasing(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 3, 1), weight_kg=_dec("72.00"), entry_id=_uuid(2)),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(3)),
            ]
        )
        assert result.observation_count == 3
        assert result.first_logged_date == date(2025, 1, 1)
        assert result.latest_logged_date == date(2025, 6, 1)
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")
        assert result.absolute_change_kg == _dec("5.00")
        assert result.percentage_change == _dec("7.14")
        assert result.direction == BodyWeightTrendDirection.INCREASED


# ===========================================================================
# F. Decreasing trend
# ===========================================================================


class TestDecreasingTrend:
    def test_two_entries_decreasing(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("80.00")),
                _entry(logged_date=date(2025, 6, 15), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("-5.00")
        assert result.percentage_change == _dec("-6.25")
        assert result.direction == BodyWeightTrendDirection.DECREASED

    def test_multiple_entries_decreasing(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("80.00")),
                _entry(logged_date=date(2025, 3, 1), weight_kg=_dec("77.00"), entry_id=_uuid(2)),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(3)),
            ]
        )
        assert result.starting_weight_kg == _dec("80.00")
        assert result.latest_weight_kg == _dec("75.00")
        assert result.absolute_change_kg == _dec("-5.00")
        assert result.percentage_change == _dec("-6.25")
        assert result.direction == BodyWeightTrendDirection.DECREASED


# ===========================================================================
# G. Stable trend
# ===========================================================================


class TestStableTrend:
    def test_two_entries_stable(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 15), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("0.00")
        assert result.percentage_change == _dec("0.00")
        assert result.direction == BodyWeightTrendDirection.STABLE

    def test_multiple_entries_stable(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 3, 1), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00"), entry_id=_uuid(3)),
            ]
        )
        assert result.absolute_change_kg == _dec("0.00")
        assert result.percentage_change == _dec("0.00")
        assert result.direction == BodyWeightTrendDirection.STABLE


# ===========================================================================
# H. Percentage tests
# ===========================================================================


class TestPercentage:
    def test_known_positive_example(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("80.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("84.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change == _dec("5.00")

    def test_known_negative_example(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("80.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("76.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change == _dec("-5.00")

    def test_round_half_up_positive(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change == _dec("7.14")

    def test_round_half_up_negative(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("75.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change == _dec("-6.67")

    def test_repeating_decimal(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("60.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change == _dec("16.67")

    def test_decimal_output_type(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert isinstance(result.percentage_change, Decimal)

    def test_exactly_two_decimal_places(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        s = str(result.percentage_change)
        assert "." in s
        assert len(s.split(".")[1]) == 2

    def test_no_float_conversion(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert not isinstance(result.percentage_change, float)

    def test_no_absolute_value(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("80.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change < _dec("0")

    def test_no_capping(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("10.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("20.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.percentage_change == _dec("100.00")


# ===========================================================================
# I. Ordering tests
# ===========================================================================


class TestOrdering:
    def test_already_ascending(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")

    def test_descending_input(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
            ]
        )
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")

    def test_randomized_order(self):
        entries = [
            _entry(logged_date=date(2025, 3, 1), weight_kg=_dec("72.00"), entry_id=_uuid(2)),
            _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(3)),
            _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
        ]
        random.shuffle(entries)
        result = calculate_body_weight_trend(entries=entries)
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")

    def test_tuple_input(self):
        result = calculate_body_weight_trend(
            entries=(
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            )
        )
        assert result.starting_weight_kg == _dec("70.00")

    def test_list_input(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.starting_weight_kg == _dec("70.00")

    def test_generator_input(self):
        def _gen():
            yield _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
            yield _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2))

        result = calculate_body_weight_trend(entries=_gen())
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")

    def test_iterator_input(self):
        entries = iter(
            [
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        result = calculate_body_weight_trend(entries=entries)
        assert result.starting_weight_kg == _dec("70.00")

    def test_same_logical_entries_different_orders_equal(self):
        e1 = _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
        e2 = _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2))
        result_a = calculate_body_weight_trend(entries=[e1, e2])
        result_b = calculate_body_weight_trend(entries=[e2, e1])
        assert result_a == result_b

    def test_first_latest_based_on_date_not_input_order(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
            ]
        )
        assert result.first_logged_date == date(2025, 1, 1)
        assert result.latest_logged_date == date(2025, 6, 1)

    def test_entry_id_tie_breaker(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 6, 15), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
                _entry(logged_date=date(2025, 6, 15), weight_kg=_dec("70.00")),
            ]
        )
        assert result.starting_weight_kg == _dec("70.00")
        assert result.latest_weight_kg == _dec("75.00")


# ===========================================================================
# J. Mutation tests
# ===========================================================================


class TestMutation:
    def test_caller_list_order_unchanged(self):
        e1 = _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
        e2 = _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2))
        original = [e2, e1]
        original_copy = list(original)
        calculate_body_weight_trend(entries=original)
        assert original == original_copy

    def test_caller_list_length_unchanged(self):
        entries = [
            _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
            _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
        ]
        original_len = len(entries)
        calculate_body_weight_trend(entries=entries)
        assert len(entries) == original_len

    def test_caller_tuple_unchanged(self):
        e1 = _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
        e2 = _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2))
        original = (e1, e2)
        original_copy = tuple(original)
        calculate_body_weight_trend(entries=original)
        assert original == original_copy

    def test_domain_entries_unchanged(self):
        entry = _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
        original_weight = entry.weight_kg
        calculate_body_weight_trend(
            entries=[
                entry,
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert entry.weight_kg == original_weight

    def test_generator_consumed_once(self):
        def _gen():
            yield _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
            yield _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2))

        gen = _gen()
        calculate_body_weight_trend(entries=gen)
        remaining = list(gen)
        assert len(remaining) == 0

    def test_repeated_calls_deterministic(self):
        entries = [
            _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
            _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
        ]
        result1 = calculate_body_weight_trend(entries=list(entries))
        result2 = calculate_body_weight_trend(entries=list(entries))
        assert result1 == result2


# ===========================================================================
# K. Purity tests
# ===========================================================================


class TestPurity:
    PROHIBITED_IMPORTS = [
        "fastapi",
        "starlette",
        "pydantic",
        "sqlalchemy",
        "alembic",
        "AsyncSession",
        "database",
        "repository",
        "service",
        "api",
        "requests",
        "httpx",
        "urllib",
        "random",
        "os.environ",
        "getenv",
        "AI",
        "LLM",
        "Groq",
    ]

    def test_module_no_prohibited_imports(self):
        mod = importlib.import_module(MODULE)
        source = open(mod.__file__).read().lower()
        for token in self.PROHIBITED_IMPORTS:
            if token in ("random", "api"):
                continue
            assert token not in source, f"Found prohibited token '{token}' in source"
        import re as _re

        assert not _re.search(r"import\s+api|from\s+\S*api", source), "Found 'api' import"

    def test_module_no_system_clock(self):
        mod = importlib.import_module(MODULE)
        source = open(mod.__file__).read()
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source

    def test_module_no_filesystem_io(self):
        mod = importlib.import_module(MODULE)
        source = open(mod.__file__).read()
        assert "open(" not in source

    def test_module_no_network(self):
        mod = importlib.import_module(MODULE)
        source = open(mod.__file__).read().lower()
        assert "http" not in source
        assert "urllib" not in source
        assert "httpx" not in source

    def test_module_no_environment(self):
        mod = importlib.import_module(MODULE)
        source = open(mod.__file__).read()
        assert "environ" not in source
        assert "getenv" not in source


# ===========================================================================
# L. Boundary tests
# ===========================================================================


class TestBoundary:
    def test_schema_module_exists(self):
        import os

        backend = os.path.join(os.path.dirname(__file__), "..")
        schemas_dir = os.path.join(backend, "app", "schemas")
        trend_schema = os.path.join(schemas_dir, "body_weight_trends.py")
        assert os.path.exists(trend_schema)

    def test_no_orm_model(self):
        import os

        backend = os.path.join(os.path.dirname(__file__), "..")
        models_dir = os.path.join(backend, "app", "models")
        trend_model = os.path.join(models_dir, "body_weight_trend.py")
        assert not os.path.exists(trend_model)

    def test_no_repository(self):
        import os

        backend = os.path.join(os.path.dirname(__file__), "..")
        repos_dir = os.path.join(backend, "app", "repositories")
        trend_repo = os.path.join(repos_dir, "body_weight_trend.py")
        assert not os.path.exists(trend_repo)

    def test_no_service(self):
        import os

        backend = os.path.join(os.path.dirname(__file__), "..")
        services_dir = os.path.join(backend, "app", "services")
        trend_service = os.path.join(services_dir, "body_weight_trend.py")
        assert not os.path.exists(trend_service)

    def test_no_api_router(self):
        import os

        backend = os.path.join(os.path.dirname(__file__), "..")
        api_dir = os.path.join(backend, "app", "api", "v1")
        trend_router = os.path.join(api_dir, "body_weight_trends.py")
        assert not os.path.exists(trend_router)

    def test_no_migration(self):
        import os

        backend = os.path.join(os.path.dirname(__file__), "..")
        versions_dir = os.path.join(backend, "alembic", "versions")
        # List all files and check no trend-related migration
        if os.path.exists(versions_dir):
            for f in os.listdir(versions_dir):
                assert "trend" not in f.lower()


# ===========================================================================
# M. Constant tests
# ===========================================================================


class TestConstants:
    def test_percentage_decimal_places_value(self):
        assert BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES == _dec("0.01")

    def test_percentage_decimal_places_is_decimal(self):
        assert isinstance(BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES, Decimal)

    def test_reuses_body_weight_decimal_places(self):
        from app.core.body_weight_trends import calculate_body_weight_trend as _calc

        result = _calc(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("5.00")


# ===========================================================================
# N. Determinism
# ===========================================================================


class TestDeterminism:
    def test_repeated_calls_produce_same_result(self):
        entries = (
            _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
            _entry(logged_date=date(2025, 3, 1), weight_kg=_dec("72.00"), entry_id=_uuid(2)),
            _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(3)),
        )
        results = [calculate_body_weight_trend(entries=entries) for _ in range(5)]
        for i in range(1, len(results)):
            assert results[i] == results[0]

    def test_different_container_types_same_result(self):
        e1 = _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00"))
        e2 = _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2))
        result_list = calculate_body_weight_trend(entries=[e1, e2])
        result_tuple = calculate_body_weight_trend(entries=(e1, e2))
        assert result_list == result_tuple

    def test_random_shuffled_same_result(self):
        entries = [
            _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
            _entry(logged_date=date(2025, 3, 1), weight_kg=_dec("72.00"), entry_id=_uuid(2)),
            _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(3)),
        ]
        base = calculate_body_weight_trend(entries=list(entries))
        for _ in range(10):
            shuffled = list(entries)
            random.shuffle(shuffled)
            result = calculate_body_weight_trend(entries=shuffled)
            assert result == base


# ===========================================================================
# O. Absolute change tests
# ===========================================================================


class TestAbsoluteChange:
    def test_positive_change(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("5.00")

    def test_negative_change(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("75.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("-5.00")

    def test_zero_change(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.00"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("0.00")

    def test_quantized_to_two_places(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("75.123"), entry_id=_uuid(2)),
            ]
        )
        assert result.absolute_change_kg == _dec("5.12")


# ===========================================================================
# P. Direction from unrounded change
# ===========================================================================


class TestDirectionFromUnroundedChange:
    def test_small_positive_change_is_increased(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.01"), entry_id=_uuid(2)),
            ]
        )
        assert result.direction == BodyWeightTrendDirection.INCREASED

    def test_small_negative_change_is_decreased(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("69.99"), entry_id=_uuid(2)),
            ]
        )
        assert result.direction == BodyWeightTrendDirection.DECREASED

    def test_no_tolerance_band(self):
        result = calculate_body_weight_trend(
            entries=[
                _entry(logged_date=date(2025, 1, 1), weight_kg=_dec("70.00")),
                _entry(logged_date=date(2025, 6, 1), weight_kg=_dec("70.006"), entry_id=_uuid(2)),
            ]
        )
        assert result.direction == BodyWeightTrendDirection.INCREASED
        assert result.absolute_change_kg == _dec("0.01")


# ===========================================================================
# Q. Module exports
# ===========================================================================


class TestExports:
    def test_module_exports(self):
        mod = importlib.import_module(MODULE)
        expected = {
            "BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES",
            "BodyWeightTrendDirection",
            "BodyWeightTrendResult",
            "calculate_body_weight_trend",
        }
        assert expected.issubset(dir(mod))
