from __future__ import annotations

import importlib
import inspect
import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.body_weight import (
    BodyWeightEntry,
)
from app.schemas.body_weight import (
    BodyWeightEntryCreate,
    BodyWeightEntryData,
    BodyWeightEntrySuccessResponse,
    BodyWeightHistoryData,
    BodyWeightHistorySuccessResponse,
)

SCHEMA_MODULE = "app.schemas.body_weight"
DOMAIN_MODULE = "app.core.body_weight"


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


# ===========================================================================
# A. Module and export contract
# ===========================================================================


class TestModuleExports:
    def test_module_imports_successfully(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        assert mod is not None

    def test_all_five_schemas_exist(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        for name in [
            "BodyWeightEntryCreate",
            "BodyWeightEntryData",
            "BodyWeightHistoryData",
            "BodyWeightEntrySuccessResponse",
            "BodyWeightHistorySuccessResponse",
        ]:
            assert hasattr(mod, name), f"Missing schema: {name}"

    def test_all_five_exported_from_app_schemas(self):
        from app.schemas import (
            BodyWeightEntryCreate,
            BodyWeightEntryData,
            BodyWeightEntrySuccessResponse,
            BodyWeightHistoryData,
            BodyWeightHistorySuccessResponse,
        )

        assert BodyWeightEntryCreate is not None
        assert BodyWeightEntryData is not None
        assert BodyWeightEntrySuccessResponse is not None
        assert BodyWeightHistoryData is not None
        assert BodyWeightHistorySuccessResponse is not None

    def test_no_unexpected_public_body_weight_schema_names(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        expected = [
            "BodyWeightDeleteSuccessResponse",
            "BodyWeightEntryCreate",
            "BodyWeightEntryData",
            "BodyWeightHistoryData",
            "BodyWeightEntrySuccessResponse",
            "BodyWeightHistorySuccessResponse",
        ]
        all_exports = mod.__all__
        assert sorted(all_exports) == sorted(expected)

    def test_no_duplicate_domain_constants_or_types(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        # Should not redefine domain constants
        assert "MIN_BODY_WEIGHT_KG = " not in source
        assert "MAX_BODY_WEIGHT_KG = " not in source
        assert "BODY_WEIGHT_DECIMAL_PLACES = " not in source
        # Should not redefine domain type
        assert "class BodyWeightEntry:" not in source


# ===========================================================================
# B. BodyWeightEntryCreate
# ===========================================================================


class TestBodyWeightEntryCreateFieldSet:
    def test_exact_field_set(self):
        fields = set(BodyWeightEntryCreate.model_fields)
        assert fields == {"weight_kg"}

    def test_weight_kg_required(self):
        assert BodyWeightEntryCreate.model_fields["weight_kg"].is_required()

    def test_no_default(self):
        assert BodyWeightEntryCreate.model_fields["weight_kg"].is_required()

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=Decimal("70.00"), extra_field="value")  # type: ignore[call-arg]

    def test_valid_decimal_accepted(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("70.00"))
        assert obj.weight_kg == _dec("70.00")

    def test_valid_integer_accepted(self):
        obj = BodyWeightEntryCreate(weight_kg=70)
        assert obj.weight_kg == _dec("70.00")

    def test_valid_numeric_string_accepted(self):
        obj = BodyWeightEntryCreate(weight_kg="70.00")
        assert obj.weight_kg == _dec("70.00")

    def test_valid_finite_float_accepted(self):
        obj = BodyWeightEntryCreate(weight_kg=70.5)
        assert obj.weight_kg == _dec("70.50")

    def test_missing_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate()  # type: ignore[call-arg]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=None)  # type: ignore[arg-type]

    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="valid decimal"):
            BodyWeightEntryCreate(weight_kg=True)

    def test_nan_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightEntryCreate(weight_kg=Decimal("NaN"))

    def test_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightEntryCreate(weight_kg=Decimal("Infinity"))

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError, match="finite"):
            BodyWeightEntryCreate(weight_kg=Decimal("-Infinity"))

    def test_below_minimum_rejected(self):
        with pytest.raises(ValidationError, match="at least"):
            BodyWeightEntryCreate(weight_kg=Decimal("9.99"))

    def test_exact_minimum_accepted(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("10.00"))
        assert obj.weight_kg == _dec("10.00")

    def test_exact_maximum_accepted(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("700.00"))
        assert obj.weight_kg == _dec("700.00")

    def test_above_maximum_rejected(self):
        with pytest.raises(ValidationError, match="at most"):
            BodyWeightEntryCreate(weight_kg=Decimal("700.01"))

    def test_two_decimal_normalization(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("70.1"))
        assert obj.weight_kg == _dec("70.10")

    def test_round_half_up_behavior(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("70.125"))
        assert obj.weight_kg == _dec("70.13")

    def test_round_half_up_down(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("70.124"))
        assert obj.weight_kg == _dec("70.12")

    def test_boundary_after_rounding_above_min(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("9.995"))
        assert obj.weight_kg == _dec("10.00")

    def test_boundary_after_rounding_below_min_rejected(self):
        with pytest.raises(ValidationError, match="at least"):
            BodyWeightEntryCreate(weight_kg=Decimal("9.994"))

    def test_boundary_after_rounding_below_max(self):
        obj = BodyWeightEntryCreate(weight_kg=Decimal("699.995"))
        assert obj.weight_kg == _dec("700.00")

    def test_boundary_after_rounding_above_max_rejected(self):
        with pytest.raises(ValidationError, match="at most"):
            BodyWeightEntryCreate(weight_kg=Decimal("700.005"))

    def test_entry_id_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=Decimal("70.00"), entry_id=_uuid())  # type: ignore[call-arg]

    def test_logged_date_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=Decimal("70.00"), logged_date=date(2025, 6, 15))  # type: ignore[call-arg]

    def test_user_id_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=Decimal("70.00"), user_id=_uuid())  # type: ignore[call-arg]

    def test_created_at_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=Decimal("70.00"), created_at="2025-06-15T00:00:00")  # type: ignore[call-arg]

    def test_updated_at_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryCreate(weight_kg=Decimal("70.00"), updated_at="2025-06-15T00:00:00")  # type: ignore[call-arg]

    def test_caller_input_not_mutated(self):
        val = Decimal("70.00")
        original = val.copy_abs()
        BodyWeightEntryCreate(weight_kg=val)
        assert val == original


# ===========================================================================
# C. BodyWeightEntryData
# ===========================================================================


class TestBodyWeightEntryDataFieldSet:
    def test_exact_field_set(self):
        fields = set(BodyWeightEntryData.model_fields)
        assert fields == {"entry_id", "logged_date", "weight_kg"}, f"Got {fields}"

    def test_valid_construction(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert obj.entry_id == _uuid()
        assert obj.logged_date == date(2025, 6, 15)
        assert obj.weight_kg == _dec("70.00")

    def test_uuid_validation(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id="not-a-uuid",  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_uuid_string_accepted(self):
        obj = BodyWeightEntryData(
            entry_id=str(_uuid()),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert obj.entry_id == _uuid()

    def test_pure_date_from_string(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date="2025-06-15",
            weight_kg=Decimal("70.00"),
        )
        assert obj.logged_date == date(2025, 6, 15)

    def test_pure_date_type_preserved(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        assert isinstance(obj.logged_date, date)
        assert not isinstance(obj.logged_date, datetime)

    def test_decimal_validation(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("999.99"),
            )

    def test_missing_entry_id_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_missing_logged_date_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=_uuid(),
                weight_kg=Decimal("70.00"),
            )

    def test_missing_weight_kg_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
            )

    def test_null_entry_id_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=None,  # type: ignore[arg-type]
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )

    def test_null_logged_date_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=None,  # type: ignore[arg-type]
                weight_kg=Decimal("70.00"),
            )

    def test_null_weight_kg_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=None,  # type: ignore[arg-type]
            )

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_frozen_top_level(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        with pytest.raises(ValidationError):
            obj.weight_kg = Decimal("80.00")  # type: ignore[misc]

    def test_from_attributes_true(self):
        assert BodyWeightEntryData.model_config.get("from_attributes") is True

    def test_orm_like_object_conversion(self):
        class _Fake:
            def __init__(self):
                self.entry_id = _uuid()
                self.logged_date = date(2025, 6, 15)
                self.weight_kg = Decimal("70.00")

        fake = _Fake()
        obj = BodyWeightEntryData.model_validate(fake, from_attributes=True)
        assert obj.entry_id == _uuid()
        assert obj.logged_date == date(2025, 6, 15)
        assert obj.weight_kg == _dec("70.00")

    def test_dict_conversion(self):
        data = {
            "entry_id": str(_uuid()),
            "logged_date": "2025-06-15",
            "weight_kg": "70.00",
        }
        obj = BodyWeightEntryData.model_validate(data)
        assert obj.entry_id == _uuid()
        assert obj.logged_date == date(2025, 6, 15)
        assert obj.weight_kg == _dec("70.00")

    def test_no_user_id_exposure(self):
        assert "user_id" not in BodyWeightEntryData.model_fields

    def test_no_timestamps(self):
        assert "created_at" not in BodyWeightEntryData.model_fields
        assert "updated_at" not in BodyWeightEntryData.model_fields

    def test_no_sqlalchemy_state_exposure(self):
        assert "_sa_instance_state" not in BodyWeightEntryData.model_fields

    def test_decimal_preserved_in_python(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        dumped = obj.model_dump()
        assert isinstance(dumped["weight_kg"], Decimal)

    def test_decimal_json_serialization(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["weight_kg"] == "70.00"

    def test_uuid_json_serialization(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["entry_id"] == str(_uuid())

    def test_date_json_serialization(self):
        obj = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        raw = obj.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["logged_date"] == "2025-06-15"


# ===========================================================================
# D. Entry conversion helper
# ===========================================================================


class TestBodyWeightEntryDataFromDomain:
    def test_domain_converts_exactly(self):
        entry = _entry()
        data = BodyWeightEntryData.from_domain(entry)
        assert data.entry_id == entry.entry_id
        assert data.logged_date == entry.logged_date
        assert data.weight_kg == entry.weight_kg

    def test_all_values_copied_exactly(self):
        uid = _uuid2()
        d = date(2025, 1, 1)
        w = Decimal("65.50")
        entry = BodyWeightEntry(entry_id=uid, logged_date=d, weight_kg=w)
        data = BodyWeightEntryData.from_domain(entry)
        assert data.entry_id is uid
        assert data.logged_date is d
        assert data.weight_kg == w

    def test_no_recalculation(self):
        entry = _entry(weight_kg=Decimal("70.125"))
        data = BodyWeightEntryData.from_domain(entry)
        assert data.weight_kg == _dec("70.13")  # Already normalized by domain, not recalculated

    def test_no_mutation(self):
        entry = _entry()
        original_id = entry.entry_id
        original_date = entry.logged_date
        original_weight = entry.weight_kg
        BodyWeightEntryData.from_domain(entry)
        assert entry.entry_id == original_id
        assert entry.logged_date == original_date
        assert entry.weight_kg == original_weight

    def test_deterministic_output(self):
        entry = _entry()
        r1 = BodyWeightEntryData.from_domain(entry)
        r2 = BodyWeightEntryData.from_domain(entry)
        assert r1.model_dump() == r2.model_dump()

    def test_invalid_non_domain_object_rejected(self):
        with pytest.raises(TypeError, match="BodyWeightEntry"):
            BodyWeightEntryData.from_domain("not an entry")  # type: ignore[arg-type]


# ===========================================================================
# E. BodyWeightHistoryData
# ===========================================================================


class TestBodyWeightHistoryDataFieldSet:
    def test_exact_field_set(self):
        fields = set(BodyWeightHistoryData.model_fields)
        assert fields == {"entries"}

    def test_entries_required(self):
        assert BodyWeightHistoryData.model_fields["entries"].is_required()

    def test_empty_history_accepted(self):
        obj = BodyWeightHistoryData(entries=())
        assert obj.entries == ()

    def test_empty_list_accepted(self):
        obj = BodyWeightHistoryData(entries=[])
        assert obj.entries == ()

    def test_one_entry_accepted(self):
        entry_data = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        obj = BodyWeightHistoryData(entries=(entry_data,))
        assert len(obj.entries) == 1

    def test_multiple_entries_accepted(self):
        e1 = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        e2 = BodyWeightEntryData(
            entry_id=_uuid2(),
            logged_date=date(2025, 1, 1),
            weight_kg=Decimal("71.00"),
        )
        obj = BodyWeightHistoryData(entries=(e1, e2))
        assert len(obj.entries) == 2

    def test_tuple_input_accepted(self):
        obj = BodyWeightHistoryData(entries=())
        assert isinstance(obj.entries, tuple)

    def test_list_input_stored_as_tuple(self):
        obj = BodyWeightHistoryData(entries=[])
        assert isinstance(obj.entries, tuple)

    def test_exact_order_preserved(self):
        e1 = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        e2 = BodyWeightEntryData(
            entry_id=_uuid2(),
            logged_date=date(2025, 1, 1),
            weight_kg=Decimal("71.00"),
        )
        obj = BodyWeightHistoryData(entries=[e1, e2])
        assert obj.entries[0].entry_id == e1.entry_id
        assert obj.entries[1].entry_id == e2.entry_id

    def test_schema_performs_no_sorting(self):
        e1 = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        e2 = BodyWeightEntryData(
            entry_id=_uuid2(),
            logged_date=date(2025, 1, 1),
            weight_kg=Decimal("71.00"),
        )
        obj = BodyWeightHistoryData(entries=[e2, e1])
        assert obj.entries[0].entry_id == e2.entry_id
        assert obj.entries[1].entry_id == e1.entry_id

    def test_duplicate_date_rejected(self):
        e1 = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        e2 = BodyWeightEntryData(
            entry_id=_uuid2(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("71.00"),
        )
        with pytest.raises(ValidationError, match="Duplicate logged_date"):
            BodyWeightHistoryData(entries=[e1, e2])

    def test_duplicate_entry_id_rejected(self):
        e1 = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        e2 = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 1, 1),
            weight_kg=Decimal("71.00"),
        )
        with pytest.raises(ValidationError, match="Duplicate entry_id"):
            BodyWeightHistoryData(entries=[e1, e2])

    def test_missing_entries_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightHistoryData()  # type: ignore[call-arg]

    def test_null_entries_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightHistoryData(entries=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightHistoryData(
                entries=(),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_top_level_model_frozen(self):
        obj = BodyWeightHistoryData(entries=())
        with pytest.raises(ValidationError):
            obj.entries = (
                BodyWeightEntryData(  # type: ignore[misc]
                    entry_id=_uuid(),
                    logged_date=date(2025, 6, 15),
                    weight_kg=Decimal("70.00"),
                ),
            )

    def test_nested_models_frozen(self):
        e = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        obj = BodyWeightHistoryData(entries=(e,))
        with pytest.raises(ValidationError):
            obj.entries[0].weight_kg = Decimal("80.00")  # type: ignore[misc]

    def test_caller_owned_list_not_mutated(self):
        lst = []
        original = list(lst)
        BodyWeightHistoryData(entries=lst)
        assert lst == original


# ===========================================================================
# F. BodyWeightHistoryData.from_domain
# ===========================================================================


class TestBodyWeightHistoryDataFromDomain:
    def test_empty_domain_history(self):
        result = BodyWeightHistoryData.from_domain([])
        assert result.entries == ()

    def test_one_entry(self):
        entry = _entry()
        result = BodyWeightHistoryData.from_domain([entry])
        assert len(result.entries) == 1
        assert result.entries[0].entry_id == entry.entry_id
        assert result.entries[0].logged_date == entry.logged_date
        assert result.entries[0].weight_kg == entry.weight_kg

    def test_multiple_entries(self):
        e1 = _entry(logged_date=date(2025, 1, 1))
        e2 = _entry(logged_date=date(2025, 6, 15), entry_id=_uuid2())
        result = BodyWeightHistoryData.from_domain([e1, e2])
        assert len(result.entries) == 2

    def test_tuple_input(self):
        result = BodyWeightHistoryData.from_domain((_entry(),))
        assert len(result.entries) == 1

    def test_list_input(self):
        result = BodyWeightHistoryData.from_domain([_entry()])
        assert len(result.entries) == 1

    def test_generator_conversion_supported(self):
        def _gen():
            yield _entry(logged_date=date(2025, 1, 1))
            yield _entry(logged_date=date(2025, 6, 15), entry_id=_uuid2())

        result = BodyWeightHistoryData.from_domain(_gen())
        assert len(result.entries) == 2

    def test_exact_order_preserved(self):
        e1 = _entry(logged_date=date(2025, 6, 15))
        e2 = _entry(logged_date=date(2025, 1, 1), entry_id=_uuid2())
        result = BodyWeightHistoryData.from_domain([e1, e2])
        assert result.entries[0].entry_id == e1.entry_id
        assert result.entries[1].entry_id == e2.entry_id

    def test_not_calling_domain_sorting(self):
        e1 = _entry(logged_date=date(2025, 6, 15))
        e2 = _entry(logged_date=date(2025, 1, 1), entry_id=_uuid2())
        result = BodyWeightHistoryData.from_domain([e1, e2])
        # order is [e1, e2] (original), not sorted by date
        assert result.entries[0].logged_date == date(2025, 6, 15)

    def test_nested_schema_conversion_correct(self):
        entry = _entry()
        result = BodyWeightHistoryData.from_domain([entry])
        assert isinstance(result.entries[0], BodyWeightEntryData)

    def test_domain_objects_not_mutated(self):
        e1 = _entry(logged_date=date(2025, 1, 1))
        e2 = _entry(entry_id=_uuid2(), logged_date=date(2025, 6, 15))
        original_ids = [e1.entry_id, e2.entry_id]
        original_dates = [e1.logged_date, e2.logged_date]
        original_weights = [e1.weight_kg, e2.weight_kg]
        BodyWeightHistoryData.from_domain([e1, e2])
        assert e1.entry_id == original_ids[0]
        assert e2.entry_id == original_ids[1]
        assert e1.logged_date == original_dates[0]
        assert e2.logged_date == original_dates[1]
        assert e1.weight_kg == original_weights[0]
        assert e2.weight_kg == original_weights[1]

    def test_deterministic_output(self):
        entries = [_entry(), _entry(entry_id=_uuid2(), logged_date=date(2025, 1, 1))]
        r1 = BodyWeightHistoryData.from_domain(entries)
        r2 = BodyWeightHistoryData.from_domain(entries)
        assert r1.model_dump() == r2.model_dump()


# ===========================================================================
# G. Success responses - BodyWeightEntrySuccessResponse
# ===========================================================================


class TestBodyWeightEntrySuccessResponse:
    def test_default_success_is_true(self):
        resp = BodyWeightEntrySuccessResponse(
            data=BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )
        )
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntrySuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=BodyWeightEntryData(
                    entry_id=_uuid(),
                    logged_date=date(2025, 6, 15),
                    weight_kg=Decimal("70.00"),
                ),
            )

    def test_exact_default_message(self):
        resp = BodyWeightEntrySuccessResponse(
            data=BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            )
        )
        assert resp.message == "Body-weight entry processed successfully."

    def test_custom_message_accepted(self):
        resp = BodyWeightEntrySuccessResponse(
            message="Custom message.",
            data=BodyWeightEntryData(
                entry_id=_uuid(),
                logged_date=date(2025, 6, 15),
                weight_kg=Decimal("70.00"),
            ),
        )
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            BodyWeightEntrySuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntrySuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightEntrySuccessResponse(
                data=BodyWeightEntryData(
                    entry_id=_uuid(),
                    logged_date=date(2025, 6, 15),
                    weight_kg=Decimal("70.00"),
                ),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_nested_serialization_correct(self):
        entry_data = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        resp = BodyWeightEntrySuccessResponse(data=entry_data)
        dumped = resp.model_dump()
        assert dumped["success"] is True
        assert dumped["message"] == "Body-weight entry processed successfully."
        assert dumped["data"]["entry_id"] == _uuid()
        assert dumped["data"]["logged_date"] == date(2025, 6, 15)
        assert dumped["data"]["weight_kg"] == _dec("70.00")

    def test_json_serialization(self):
        entry_data = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        resp = BodyWeightEntrySuccessResponse(data=entry_data)
        raw = resp.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["success"] is True
        assert parsed["message"] == "Body-weight entry processed successfully."
        assert parsed["data"]["entry_id"] == str(_uuid())
        assert parsed["data"]["logged_date"] == "2025-06-15"
        assert parsed["data"]["weight_kg"] == "70.00"


# ===========================================================================
# H. Success responses - BodyWeightHistorySuccessResponse
# ===========================================================================


class TestBodyWeightHistorySuccessResponse:
    def test_default_success_is_true(self):
        resp = BodyWeightHistorySuccessResponse(data=BodyWeightHistoryData(entries=()))
        assert resp.success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightHistorySuccessResponse(
                success=False,  # type: ignore[arg-type]
                data=BodyWeightHistoryData(entries=()),
            )

    def test_exact_default_message(self):
        resp = BodyWeightHistorySuccessResponse(data=BodyWeightHistoryData(entries=()))
        assert resp.message == "Body-weight history retrieved successfully."

    def test_custom_message_accepted(self):
        resp = BodyWeightHistorySuccessResponse(
            message="Custom message.",
            data=BodyWeightHistoryData(entries=()),
        )
        assert resp.message == "Custom message."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            BodyWeightHistorySuccessResponse()  # type: ignore[call-arg]

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightHistorySuccessResponse(data=None)  # type: ignore[arg-type]

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            BodyWeightHistorySuccessResponse(
                data=BodyWeightHistoryData(entries=()),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_nested_serialization_correct(self):
        entry_data = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        history = BodyWeightHistoryData(entries=[entry_data])
        resp = BodyWeightHistorySuccessResponse(data=history)
        dumped = resp.model_dump()
        assert dumped["success"] is True
        assert dumped["message"] == "Body-weight history retrieved successfully."
        assert len(dumped["data"]["entries"]) == 1

    def test_json_serialization(self):
        entry_data = BodyWeightEntryData(
            entry_id=_uuid(),
            logged_date=date(2025, 6, 15),
            weight_kg=Decimal("70.00"),
        )
        history = BodyWeightHistoryData(entries=[entry_data])
        resp = BodyWeightHistorySuccessResponse(data=history)
        raw = resp.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["success"] is True
        assert parsed["message"] == "Body-weight history retrieved successfully."
        assert len(parsed["data"]["entries"]) == 1
        assert parsed["data"]["entries"][0]["entry_id"] == str(_uuid())
        assert parsed["data"]["entries"][0]["logged_date"] == "2025-06-15"
        assert parsed["data"]["entries"][0]["weight_kg"] == "70.00"


# ===========================================================================
# I. Architecture and purity
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
        for token in ("groq", "openai", "langchain", "gemini", "llm"):
            assert token not in source.lower()

    def test_no_usda(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "usda" not in source.lower()

    def test_no_bmi_formula(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "bmi" not in source.lower()

    def test_no_bmr_formula(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "bmr" not in source.lower()

    def test_no_tdee_formula(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "tdee" not in source.lower()

    def test_no_weight_change_formula(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "weight_change" not in source.lower()

    def test_no_percentage_change(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "percentage" not in source.lower()

    def test_no_trend_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "trend" not in source.lower()

    def test_no_prediction_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "predict" not in source.lower()

    def test_no_recommendation_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "recommend" not in source.lower()

    def test_no_persistence_logic(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "persist" not in source.lower()
        assert "commit" not in source.lower()
        assert "flush" not in source.lower()

    def test_only_allowed_imports(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        allowed = (
            "from __future__",
            "from collections.abc",
            "from datetime",
            "from decimal",
            "from typing",
            "from uuid",
            "from pydantic",
            "from app.core.body_weight",
        )
        lines = [
            ln for ln in source.splitlines() if ln.startswith("import ") or ln.startswith("from ")
        ]
        for ln in lines:
            assert any(ln.startswith(a) for a in allowed), f"unexpected import: {ln!r}"


# ===========================================================================
# J. Dependency direction
# ===========================================================================


class TestDependencyDirection:
    def test_schema_may_import_domain(self):
        source = inspect.getsource(importlib.import_module(SCHEMA_MODULE))
        assert "from app.core.body_weight" in source

    def test_domain_must_not_import_pydantic(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "pydantic" not in source.lower()

    def test_domain_must_not_import_schema_module(self):
        source = inspect.getsource(importlib.import_module(DOMAIN_MODULE))
        assert "from app.schemas" not in source

    def test_no_circular_dependency(self):
        import app.core.body_weight
        import app.schemas.body_weight

        assert app.core.body_weight is not None
        assert app.schemas.body_weight is not None


# ===========================================================================
# K. Regression and phase boundary
# ===========================================================================


class TestPhaseBoundaries:
    def test_body_weight_orm_model_exists(self):
        import os

        model_path = "app/models/body_weight.py"
        assert os.path.exists(model_path)

    def test_body_weight_migration_exists(self):
        import os

        migration_dir = "alembic/versions"
        files = [f for f in os.listdir(migration_dir) if f.endswith(".py") and f != "__init__.py"]
        body_weight_migrations = [f for f in files if "body_weight" in f or "body-weight" in f]
        assert len(body_weight_migrations) == 1

    def test_body_weight_repository_exists(self):
        import os

        repo_path = "app/repositories/body_weight.py"
        assert os.path.exists(repo_path)

    def test_body_weight_service_exists(self):
        import os

        service_path = "app/services/body_weight.py"
        assert os.path.exists(service_path)

    def test_body_weight_api_router_exists(self):
        import os

        router_path = "app/api/v1/body_weights.py"
        assert os.path.exists(router_path)

    def test_body_weight_endpoint_in_openapi(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        body_weight_paths = [p for p in paths if "body-weight" in p or "body_weight" in p]
        assert len(body_weight_paths) == 4

    def test_body_weight_routes_appear(self):
        from app.main import create_app

        app = create_app()
        routes = [r.path for r in app.routes]
        body_weight_routes = [p for p in routes if "body-weight" in p or "body_weight" in p]
        assert len(body_weight_routes) >= 2

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
        assert len(bearer_schemes) == 1, f"Expected 1 BearerAuth scheme, got {len(bearer_schemes)}"

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
        assert actual_api_paths == expected_api_paths, f"API route mismatch: {actual_api_paths}"

    def test_orm_metadata_updated(self):
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

    def test_migration_head_updated(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        assert head == "0295723946b2"
