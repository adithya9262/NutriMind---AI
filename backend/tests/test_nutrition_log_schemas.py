from __future__ import annotations

import importlib
import inspect
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.nutrition_logs import (
    MAX_CALORIES_KCAL,
    MAX_CARBOHYDRATE_G,
    MAX_FAT_G,
    MAX_PROTEIN_G,
    MEAL_TYPE_ORDER,
    DailyNutritionLogSummary,
    DailyNutritionTotals,
    MealNutritionSummary,
    MealType,
    NutritionLogEntry,
)
from app.schemas.nutrition_logs import (
    DailyNutritionLogSuccessResponse,
    DailyNutritionLogSummaryData,
    DailyNutritionTotalsData,
    MealNutritionSummaryData,
    NutritionLogEntryCreate,
    NutritionLogEntryData,
)

SCHEMA_MODULE = "app.schemas.nutrition_logs"
DOMAIN_MODULE = "app.core.nutrition_logs"


# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def _valid_create_dict(overrides: dict | None = None) -> dict:
    d = {
        "entry_id": str(_uuid()),
        "food_name": "Oatmeal",
        "meal_type": "breakfast",
        "serving_description": "1 bowl",
        "calories_kcal": "300",
        "protein_g": "10",
        "carbohydrate_g": "50",
        "fat_g": "5",
    }
    if overrides:
        d.update(overrides)
    return d


def _valid_entry() -> NutritionLogEntry:
    return NutritionLogEntry(
        entry_id=_uuid(),
        food_name="Oatmeal",
        meal_type=MealType.BREAKFAST,
        serving_description="1 bowl",
        calories_kcal=_dec("300"),
        protein_g=_dec("10"),
        carbohydrate_g=_dec("50"),
        fat_g=_dec("5"),
    )


def _valid_totals() -> DailyNutritionTotals:
    return DailyNutritionTotals(
        calories_kcal=_dec("300"),
        protein_g=_dec("10"),
        carbohydrate_g=_dec("50"),
        fat_g=_dec("5"),
    )


def _valid_meal_summary(
    meal_type: MealType = MealType.BREAKFAST,
) -> MealNutritionSummary:
    return MealNutritionSummary(
        meal_type=meal_type,
        entry_count=1,
        totals=_valid_totals(),
    )


def _valid_log_summary() -> DailyNutritionLogSummary:
    return DailyNutritionLogSummary(
        entry_count=4,
        totals=_valid_totals(),
        meals=(
            _valid_meal_summary(MealType.BREAKFAST),
            _valid_meal_summary(MealType.LUNCH),
            _valid_meal_summary(MealType.DINNER),
            _valid_meal_summary(MealType.SNACK),
        ),
    )


def _valid_summary_data_dict(overrides: dict | None = None) -> dict:
    d = {
        "entry_count": 4,
        "totals": {
            "calories_kcal": "300",
            "protein_g": "10",
            "carbohydrate_g": "50",
            "fat_g": "5",
        },
        "meals": [
            {
                "meal_type": "breakfast",
                "entry_count": 1,
                "totals": {
                    "calories_kcal": "300",
                    "protein_g": "10",
                    "carbohydrate_g": "50",
                    "fat_g": "5",
                },
            },
            {
                "meal_type": "lunch",
                "entry_count": 1,
                "totals": {
                    "calories_kcal": "300",
                    "protein_g": "10",
                    "carbohydrate_g": "50",
                    "fat_g": "5",
                },
            },
            {
                "meal_type": "dinner",
                "entry_count": 1,
                "totals": {
                    "calories_kcal": "300",
                    "protein_g": "10",
                    "carbohydrate_g": "50",
                    "fat_g": "5",
                },
            },
            {
                "meal_type": "snack",
                "entry_count": 1,
                "totals": {
                    "calories_kcal": "300",
                    "protein_g": "10",
                    "carbohydrate_g": "50",
                    "fat_g": "5",
                },
            },
        ],
    }
    if overrides:
        d.update(overrides)
    return d


# ===========================================================================
# 1. Module and exports
# ===========================================================================


class TestModuleExports:
    def test_module_imports_successfully(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        assert mod is not None

    def test_required_schemas_exist(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        for name in [
            "NutritionLogEntryCreate",
            "NutritionLogEntryData",
            "DailyNutritionTotalsData",
            "MealNutritionSummaryData",
            "DailyNutritionLogSummaryData",
            "DailyNutritionLogSuccessResponse",
        ]:
            assert hasattr(mod, name), f"Missing schema: {name}"

    def test_all_schemas_exported_from_app_schemas(self):
        from app.schemas import (
            DailyNutritionLogSuccessResponse,
            DailyNutritionLogSummaryData,
            DailyNutritionTotalsData,
            MealNutritionSummaryData,
            NutritionLogEntryCreate,
            NutritionLogEntryData,
        )

        assert NutritionLogEntryCreate is not None
        assert NutritionLogEntryData is not None
        assert DailyNutritionTotalsData is not None
        assert MealNutritionSummaryData is not None
        assert DailyNutritionLogSummaryData is not None
        assert DailyNutritionLogSuccessResponse is not None

    def test_no_existing_export_removed(self):
        from app.schemas import (
            AccessTokenData,
        )

        assert AccessTokenData is not None

    def test_no_duplicate_meal_type(self):
        from app.schemas.nutrition_logs import MealType as SchemaMealType

        assert SchemaMealType is MealType

    def test_no_duplicate_domain_dataclass(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "class NutritionLogEntry:" not in source
        assert "class DailyNutritionTotals:" not in source
        assert "class MealNutritionSummary:" not in source
        assert "class DailyNutritionLogSummary:" not in source

    def test_no_duplicate_nutrition_constants(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert 'Decimal("10000")' not in source or "MAX_CALORIES_KCAL" in source
        assert 'Decimal("1000")' not in source or "MAX_PROTEIN_G" in source


# ===========================================================================
# 2. NutritionLogEntryCreate
# ===========================================================================


class TestNutritionLogEntryCreateFieldSet:
    def test_exact_field_set(self):
        fields = set(NutritionLogEntryCreate.model_fields)
        expected = {
            "entry_id",
            "food_name",
            "meal_type",
            "serving_description",
            "calories_kcal",
            "protein_g",
            "carbohydrate_g",
            "fat_g",
        }
        assert fields == expected

    def test_all_fields_required(self):
        for name, field in NutritionLogEntryCreate.model_fields.items():
            assert field.is_required(), f"{name} should be required"

    def test_no_defaults(self):
        for name, field in NutritionLogEntryCreate.model_fields.items():
            assert field.is_required(), f"{name} should be required"
            assert field.default_factory is None, f"{name} should have no default factory"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict(), extra_field="value")

    def test_frozen(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict())
        with pytest.raises(ValidationError):
            obj.food_name = "Changed"

    def test_valid_construction(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict())
        assert obj.food_name == "Oatmeal"
        assert obj.serving_description == "1 bowl"

    def test_valid_json_like_input(self):
        obj = NutritionLogEntryCreate.model_validate(_valid_create_dict())
        assert obj.food_name == "Oatmeal"

    def test_uuid_object_accepted(self):
        uid = _uuid()
        d = _valid_create_dict({"entry_id": uid})
        obj = NutritionLogEntryCreate(**d)
        assert obj.entry_id == uid

    def test_uuid_string_accepted_and_parsed(self):
        uid_str = str(_uuid())
        d = _valid_create_dict({"entry_id": uid_str})
        obj = NutritionLogEntryCreate(**d)
        assert obj.entry_id == UUID(uid_str)

    def test_invalid_uuid_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"entry_id": "not-a-uuid"}))

    def test_uuid_not_generated_internally(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "uuid4" not in source
        assert "uuid1" not in source
        assert "uuid7" not in source

    def test_no_forbidden_fields(self):
        d = _valid_create_dict()
        assert "user_id" not in d
        assert "created_at" not in d
        assert "updated_at" not in d


class TestNutritionLogEntryCreateMealType:
    def test_meal_type_member_accepted(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"meal_type": MealType.BREAKFAST}))
        assert obj.meal_type is MealType.BREAKFAST

    def test_lowercase_string_accepted_and_parsed(self):
        for mt in MealType:
            obj = NutritionLogEntryCreate(**_valid_create_dict({"meal_type": mt.value}))
            assert obj.meal_type is mt

    def test_invalid_meal_string_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"meal_type": "brunch"}))

    def test_missing_meal_rejected(self):
        d = _valid_create_dict()
        del d["meal_type"]
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**d)


class TestNutritionLogEntryCreateTextValidation:
    def test_food_name_trimming(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"food_name": "  Oatmeal  "}))
        assert obj.food_name == "Oatmeal"

    def test_serving_description_trimming(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"serving_description": "  1 bowl  "}))
        assert obj.serving_description == "1 bowl"

    def test_capitalization_preserved(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"food_name": "OATMEAL with Berries"}))
        assert obj.food_name == "OATMEAL with Berries"

    def test_internal_whitespace_preserved(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"food_name": "Oat  meal"}))
        assert obj.food_name == "Oat  meal"

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"food_name": ""}))

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"food_name": "   "}))

    def test_null_byte_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"food_name": "Food\0name"}))

    def test_control_characters_rejected(self):
        for code in range(32):
            with pytest.raises(ValidationError):
                NutritionLogEntryCreate(**_valid_create_dict({"food_name": f"Food{chr(code)}name"}))

    def test_del_character_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"food_name": f"Food{chr(127)}name"}))

    def test_exact_max_length_accepted(self):
        food = "A" * 200
        obj = NutritionLogEntryCreate(**_valid_create_dict({"food_name": food}))
        assert obj.food_name == food

    def test_over_max_length_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"food_name": "A" * 201}))


class TestNutritionLogEntryCreateDecimalValidation:
    def test_decimal_input_accepted(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": _dec("300")}))
        assert obj.calories_kcal == _dec("300.00")

    def test_integer_input_accepted(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": 300}))
        assert obj.calories_kcal == _dec("300.00")

    def test_string_decimal_input_accepted(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": "300.50"}))
        assert obj.calories_kcal == _dec("300.50")

    def test_bool_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": True}))

    def test_nan_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": Decimal("NaN")}))

    def test_positive_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": Decimal("Infinity")}))

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": Decimal("-Infinity")}))

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(**_valid_create_dict({"calories_kcal": _dec("-1")}))

    def test_zero_accepted(self):
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "calories_kcal": "0",
                    "protein_g": "0",
                    "carbohydrate_g": "0",
                    "fat_g": "0",
                }
            )
        )
        assert obj.calories_kcal == _dec("0.00")

    def test_exact_maximum_accepted(self):
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "calories_kcal": str(MAX_CALORIES_KCAL),
                    "protein_g": str(MAX_PROTEIN_G),
                    "carbohydrate_g": str(MAX_CARBOHYDRATE_G),
                    "fat_g": str(MAX_FAT_G),
                }
            )
        )
        assert obj.calories_kcal == MAX_CALORIES_KCAL
        assert obj.protein_g == MAX_PROTEIN_G
        assert obj.carbohydrate_g == MAX_CARBOHYDRATE_G
        assert obj.fat_g == MAX_FAT_G

    def test_above_maximum_rejected(self):
        with pytest.raises(ValidationError):
            NutritionLogEntryCreate(
                **_valid_create_dict({"calories_kcal": str(MAX_CALORIES_KCAL + _dec("0.01"))})
            )

    def test_two_decimal_normalization(self):
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "calories_kcal": "100.5",
                    "protein_g": "10.123",
                    "carbohydrate_g": "10.456",
                    "fat_g": "5.789",
                }
            )
        )
        assert obj.calories_kcal == _dec("100.50")
        assert obj.protein_g == _dec("10.12")
        assert obj.carbohydrate_g == _dec("10.46")
        assert obj.fat_g == _dec("5.79")

    def test_round_half_up(self):
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "calories_kcal": "100.555",
                    "protein_g": "10.555",
                    "carbohydrate_g": "10.555",
                    "fat_g": "5.555",
                }
            )
        )
        assert obj.calories_kcal == _dec("100.56")
        assert obj.protein_g == _dec("10.56")
        assert obj.carbohydrate_g == _dec("10.56")
        assert obj.fat_g == _dec("5.56")

    def test_mutation_rejected(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict())
        with pytest.raises(ValidationError):
            obj.food_name = "Changed"

    def test_no_target_fields(self):
        d = _valid_create_dict()
        assert "targets" not in d
        assert "remaining_calories" not in d
        assert "health_score" not in d


class TestNutritionLogEntryCreateToDomain:
    def test_to_domain_returns_nutrition_log_entry(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict())
        domain = obj.to_domain()
        assert isinstance(domain, NutritionLogEntry)

    def test_to_domain_all_values_copied_exactly(self):
        uid = _uuid()
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "entry_id": uid,
                    "food_name": "Oatmeal",
                    "meal_type": "breakfast",
                    "serving_description": "1 bowl",
                    "calories_kcal": "300.00",
                    "protein_g": "10.00",
                    "carbohydrate_g": "50.00",
                    "fat_g": "5.00",
                }
            )
        )
        domain = obj.to_domain()
        assert domain.entry_id == uid
        assert domain.food_name == "Oatmeal"
        assert domain.meal_type is MealType.BREAKFAST
        assert domain.serving_description == "1 bowl"
        assert domain.calories_kcal == _dec("300.00")
        assert domain.protein_g == _dec("10.00")
        assert domain.carbohydrate_g == _dec("50.00")
        assert domain.fat_g == _dec("5.00")

    def test_to_domain_same_uuid(self):
        uid = _uuid()
        obj = NutritionLogEntryCreate(**_valid_create_dict({"entry_id": uid}))
        domain = obj.to_domain()
        assert domain.entry_id == uid
        assert domain.entry_id is uid

    def test_to_domain_same_meal_type(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"meal_type": "lunch"}))
        domain = obj.to_domain()
        assert domain.meal_type is MealType.LUNCH

    def test_to_domain_same_normalized_decimals(self):
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "calories_kcal": "300.555",
                    "protein_g": "10.555",
                    "carbohydrate_g": "50.555",
                    "fat_g": "5.555",
                }
            )
        )
        domain = obj.to_domain()
        assert domain.calories_kcal == _dec("300.56")
        assert domain.protein_g == _dec("10.56")
        assert domain.carbohydrate_g == _dec("50.56")
        assert domain.fat_g == _dec("5.56")

    def test_to_domain_no_recalculation(self):
        obj = NutritionLogEntryCreate(
            **_valid_create_dict(
                {
                    "calories_kcal": "300",
                    "protein_g": "10",
                    "carbohydrate_g": "50",
                    "fat_g": "5",
                }
            )
        )
        domain = obj.to_domain()
        assert domain.calories_kcal == _dec("300.00")
        assert domain.protein_g == _dec("10.00")
        assert domain.carbohydrate_g == _dec("50.00")
        assert domain.fat_g == _dec("5.00")
        assert domain.calories_kcal != _dec("4") * _dec("10") + _dec("4") * _dec("50") + _dec(
            "9"
        ) * _dec("5")

    def test_to_domain_no_id_generation(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict({"entry_id": str(_uuid())}))
        domain1 = obj.to_domain()
        domain2 = obj.to_domain()
        assert domain1.entry_id == domain2.entry_id

    def test_to_domain_schema_unchanged(self):
        d = _valid_create_dict()
        obj = NutritionLogEntryCreate(**d)
        obj.to_domain()
        assert obj.food_name == "Oatmeal"
        assert obj.calories_kcal == _dec("300.00")

    def test_to_domain_deterministic(self):
        d = _valid_create_dict()
        obj = NutritionLogEntryCreate(**d)
        domain1 = obj.to_domain()
        domain2 = obj.to_domain()
        assert domain1 == domain2

    def test_to_domain_domain_validation_active(self):
        obj = NutritionLogEntryCreate(**_valid_create_dict())
        domain = obj.to_domain()
        assert isinstance(domain, NutritionLogEntry)
        assert domain.calories_kcal == _dec("300.00")


# ===========================================================================
# 3. NutritionLogEntryData
# ===========================================================================


class TestNutritionLogEntryData:
    def test_exact_field_set(self):
        fields = set(NutritionLogEntryData.model_fields)
        expected = {
            "entry_id",
            "food_name",
            "meal_type",
            "serving_description",
            "calories_kcal",
            "protein_g",
            "carbohydrate_g",
            "fat_g",
        }
        assert fields == expected

    def test_all_fields_required(self):
        for name, field in NutritionLogEntryData.model_fields.items():
            assert field.is_required(), f"{name} should be required"

    def test_extra_fields_rejected(self):
        from pydantic import ValidationError

        uid = _uuid()
        with pytest.raises(ValidationError):
            NutritionLogEntryData(
                entry_id=uid,
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_frozen(self):
        obj = NutritionLogEntryData(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        with pytest.raises(ValidationError):
            obj.food_name = "Changed"

    def test_decimal_preservation(self):
        obj = NutritionLogEntryData(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100.50"),
            protein_g=_dec("10.12"),
            carbohydrate_g=_dec("10.46"),
            fat_g=_dec("5.79"),
        )
        assert obj.calories_kcal == _dec("100.50")
        assert obj.protein_g == _dec("10.12")
        assert obj.carbohydrate_g == _dec("10.46")
        assert obj.fat_g == _dec("5.79")

    def test_json_serialization(self):
        obj = NutritionLogEntryData(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100.50"),
            protein_g=_dec("10.12"),
            carbohydrate_g=_dec("10.46"),
            fat_g=_dec("5.79"),
        )
        dumped = obj.model_dump()
        assert dumped["food_name"] == "Food"
        assert dumped["meal_type"] == "breakfast"

    def test_decimal_json_serialization(self):
        obj = NutritionLogEntryData(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100.50"),
            protein_g=_dec("10.12"),
            carbohydrate_g=_dec("10.46"),
            fat_g=_dec("5.79"),
        )
        dumped = obj.model_dump()
        assert isinstance(dumped["calories_kcal"], Decimal)

    def test_from_domain_correct_type_required(self):
        with pytest.raises(TypeError, match="NutritionLogEntry"):
            NutritionLogEntryData.from_domain("not an entry")  # type: ignore[arg-type]

    def test_from_domain_copies_exactly(self):
        entry = _valid_entry()
        data = NutritionLogEntryData.from_domain(entry)
        assert data.entry_id == entry.entry_id
        assert data.food_name == entry.food_name
        assert data.meal_type is entry.meal_type
        assert data.serving_description == entry.serving_description
        assert data.calories_kcal == entry.calories_kcal
        assert data.protein_g == entry.protein_g
        assert data.carbohydrate_g == entry.carbohydrate_g
        assert data.fat_g == entry.fat_g

    def test_from_domain_does_not_mutate_source(self):
        entry = _valid_entry()
        NutritionLogEntryData.from_domain(entry)
        assert entry.food_name == "Oatmeal"
        assert entry.calories_kcal == _dec("300.00")

    def test_from_domain_deterministic(self):
        entry = _valid_entry()
        d1 = NutritionLogEntryData.from_domain(entry)
        d2 = NutritionLogEntryData.from_domain(entry)
        assert d1 == d2


# ===========================================================================
# 4. DailyNutritionTotalsData
# ===========================================================================


class TestDailyNutritionTotalsData:
    def test_exact_field_set(self):
        fields = set(DailyNutritionTotalsData.model_fields)
        expected = {"calories_kcal", "protein_g", "carbohydrate_g", "fat_g"}
        assert fields == expected

    def test_all_fields_required(self):
        for name, field in DailyNutritionTotalsData.model_fields.items():
            assert field.is_required(), f"{name} should be required"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionTotalsData(
                calories_kcal=_dec("0"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_frozen(self):
        obj = DailyNutritionTotalsData(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        with pytest.raises(ValidationError):
            obj.calories_kcal = _dec("100")

    def test_zero_accepted(self):
        obj = DailyNutritionTotalsData(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        assert obj.calories_kcal == _dec("0.00")

    def test_positive_accepted(self):
        obj = DailyNutritionTotalsData(
            calories_kcal=_dec("2000"),
            protein_g=_dec("150"),
            carbohydrate_g=_dec("250"),
            fat_g=_dec("65"),
        )
        assert obj.calories_kcal == _dec("2000.00")

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionTotalsData(
                calories_kcal=_dec("-1"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            )

    def test_non_finite_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionTotalsData(
                calories_kcal=Decimal("NaN"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            )

    def test_decimal_preserved(self):
        obj = DailyNutritionTotalsData(
            calories_kcal=_dec("2000.55"),
            protein_g=_dec("150.12"),
            carbohydrate_g=_dec("250.78"),
            fat_g=_dec("65.99"),
        )
        assert obj.calories_kcal == _dec("2000.55")
        assert obj.protein_g == _dec("150.12")
        assert obj.carbohydrate_g == _dec("250.78")
        assert obj.fat_g == _dec("65.99")

    def test_json_serialization(self):
        obj = DailyNutritionTotalsData(
            calories_kcal=_dec("2000"),
            protein_g=_dec("150"),
            carbohydrate_g=_dec("250"),
            fat_g=_dec("65"),
        )
        dumped = obj.model_dump()
        assert isinstance(dumped["calories_kcal"], Decimal)

    def test_from_domain_correct_type_required(self):
        with pytest.raises(TypeError, match="DailyNutritionTotals"):
            DailyNutritionTotalsData.from_domain("not totals")  # type: ignore[arg-type]

    def test_from_domain_exact_conversion(self):
        totals = _valid_totals()
        data = DailyNutritionTotalsData.from_domain(totals)
        assert data.calories_kcal == totals.calories_kcal
        assert data.protein_g == totals.protein_g
        assert data.carbohydrate_g == totals.carbohydrate_g
        assert data.fat_g == totals.fat_g

    def test_from_domain_no_recalculation(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("500"),
            protein_g=_dec("20"),
            carbohydrate_g=_dec("50"),
            fat_g=_dec("10"),
        )
        data = DailyNutritionTotalsData.from_domain(totals)
        assert data.calories_kcal == _dec("500.00")
        assert data.calories_kcal != totals.protein_g * _dec("4") + totals.carbohydrate_g * _dec(
            "4"
        ) + totals.fat_g * _dec("9")

    def test_from_domain_no_mutation(self):
        totals = _valid_totals()
        DailyNutritionTotalsData.from_domain(totals)
        assert totals.calories_kcal == _dec("300.00")

    def test_from_domain_deterministic(self):
        totals = _valid_totals()
        d1 = DailyNutritionTotalsData.from_domain(totals)
        d2 = DailyNutritionTotalsData.from_domain(totals)
        assert d1 == d2


# ===========================================================================
# 5. MealNutritionSummaryData
# ===========================================================================


class TestMealNutritionSummaryData:
    def test_exact_field_set(self):
        fields = set(MealNutritionSummaryData.model_fields)
        expected = {"meal_type", "entry_count", "totals"}
        assert fields == expected

    def test_all_fields_required(self):
        for name, field in MealNutritionSummaryData.model_fields.items():
            assert field.is_required(), f"{name} should be required"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            MealNutritionSummaryData(
                meal_type=MealType.BREAKFAST,
                entry_count=1,
                totals=DailyNutritionTotalsData(
                    calories_kcal=_dec("0"),
                    protein_g=_dec("0"),
                    carbohydrate_g=_dec("0"),
                    fat_g=_dec("0"),
                ),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_frozen(self):
        obj = MealNutritionSummaryData(
            meal_type=MealType.BREAKFAST,
            entry_count=1,
            totals=DailyNutritionTotalsData(
                calories_kcal=_dec("0"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            ),
        )
        with pytest.raises(ValidationError):
            obj.entry_count = 2

    def test_meal_type_member_accepted(self):
        for mt in MealType:
            obj = MealNutritionSummaryData(
                meal_type=mt,
                entry_count=0,
                totals=DailyNutritionTotalsData(
                    calories_kcal=_dec("0"),
                    protein_g=_dec("0"),
                    carbohydrate_g=_dec("0"),
                    fat_g=_dec("0"),
                ),
            )
            assert obj.meal_type is mt

    def test_lowercase_enum_string_accepted(self):
        obj = MealNutritionSummaryData(
            meal_type="breakfast",
            entry_count=0,
            totals=DailyNutritionTotalsData(
                calories_kcal=_dec("0"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            ),
        )
        assert obj.meal_type is MealType.BREAKFAST

    def test_invalid_meal_rejected(self):
        with pytest.raises(ValidationError):
            MealNutritionSummaryData(
                meal_type="brunch",
                entry_count=0,
                totals=DailyNutritionTotalsData(
                    calories_kcal=_dec("0"),
                    protein_g=_dec("0"),
                    carbohydrate_g=_dec("0"),
                    fat_g=_dec("0"),
                ),
            )

    def test_entry_count_strict_int(self):
        obj = MealNutritionSummaryData(
            meal_type=MealType.BREAKFAST,
            entry_count=3,
            totals=DailyNutritionTotalsData(
                calories_kcal=_dec("0"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            ),
        )
        assert obj.entry_count == 3

    def test_entry_count_bool_rejected(self):
        with pytest.raises(ValidationError):
            MealNutritionSummaryData(
                meal_type=MealType.BREAKFAST,
                entry_count=True,  # type: ignore[arg-type]
                totals=DailyNutritionTotalsData(
                    calories_kcal=_dec("0"),
                    protein_g=_dec("0"),
                    carbohydrate_g=_dec("0"),
                    fat_g=_dec("0"),
                ),
            )

    def test_entry_count_negative_rejected(self):
        with pytest.raises(ValidationError):
            MealNutritionSummaryData(
                meal_type=MealType.BREAKFAST,
                entry_count=-1,
                totals=DailyNutritionTotalsData(
                    calories_kcal=_dec("0"),
                    protein_g=_dec("0"),
                    carbohydrate_g=_dec("0"),
                    fat_g=_dec("0"),
                ),
            )

    def test_entry_count_zero_accepted(self):
        obj = MealNutritionSummaryData(
            meal_type=MealType.BREAKFAST,
            entry_count=0,
            totals=DailyNutritionTotalsData(
                calories_kcal=_dec("0"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            ),
        )
        assert obj.entry_count == 0

    def test_nested_totals_required(self):
        with pytest.raises(ValidationError):
            MealNutritionSummaryData(
                meal_type=MealType.BREAKFAST,
                entry_count=0,
                totals=None,  # type: ignore[arg-type]
            )

    def test_nested_extra_rejected(self):
        with pytest.raises(ValidationError):
            MealNutritionSummaryData(
                meal_type=MealType.BREAKFAST,
                entry_count=0,
                totals={
                    "calories_kcal": "0",
                    "protein_g": "0",
                    "carbohydrate_g": "0",
                    "fat_g": "0",
                    "extra": "value",
                },
            )

    def test_from_domain_correct_type_required(self):
        with pytest.raises(TypeError, match="MealNutritionSummary"):
            MealNutritionSummaryData.from_domain("not summary")  # type: ignore[arg-type]

    def test_from_domain_exact_conversion(self):
        summary = _valid_meal_summary(MealType.BREAKFAST)
        data = MealNutritionSummaryData.from_domain(summary)
        assert data.meal_type is summary.meal_type
        assert data.entry_count == summary.entry_count
        assert data.totals.calories_kcal == summary.totals.calories_kcal

    def test_from_domain_uses_totals_from_domain(self):
        summary = _valid_meal_summary(MealType.LUNCH)
        data = MealNutritionSummaryData.from_domain(summary)
        assert isinstance(data.totals, DailyNutritionTotalsData)
        assert data.totals.protein_g == summary.totals.protein_g

    def test_from_domain_no_mutation(self):
        summary = _valid_meal_summary(MealType.BREAKFAST)
        MealNutritionSummaryData.from_domain(summary)
        assert summary.meal_type is MealType.BREAKFAST
        assert summary.entry_count == 1

    def test_from_domain_deterministic(self):
        summary = _valid_meal_summary(MealType.BREAKFAST)
        d1 = MealNutritionSummaryData.from_domain(summary)
        d2 = MealNutritionSummaryData.from_domain(summary)
        assert d1 == d2


# ===========================================================================
# 6. DailyNutritionLogSummaryData
# ===========================================================================


class TestDailyNutritionLogSummaryData:
    def test_exact_field_set(self):
        fields = set(DailyNutritionLogSummaryData.model_fields)
        expected = {"entry_count", "totals", "meals"}
        assert fields == expected

    def test_all_fields_required(self):
        for name, field in DailyNutritionLogSummaryData.model_fields.items():
            assert field.is_required(), f"{name} should be required"

    def test_extra_fields_rejected(self):
        d = _valid_summary_data_dict({"extra_field": "value"})
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_frozen(self):
        obj = DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        with pytest.raises(ValidationError):
            obj.entry_count = 5

    def test_strict_non_negative_entry_count(self):
        obj = DailyNutritionLogSummaryData(**_valid_summary_data_dict({"entry_count": 5}))
        assert obj.entry_count == 5

    def test_entry_count_bool_rejected(self):
        d = _valid_summary_data_dict({"entry_count": True})
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_entry_count_negative_rejected(self):
        d = _valid_summary_data_dict({"entry_count": -1})
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_totals_required(self):
        d = _valid_summary_data_dict()
        del d["totals"]
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_meals_required(self):
        d = _valid_summary_data_dict()
        del d["meals"]
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_tuple_output(self):
        obj = DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        assert isinstance(obj.meals, tuple)

    def test_exactly_four_meals(self):
        d = _valid_summary_data_dict()
        d["meals"] = d["meals"][:3]
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_exact_order_accepted(self):
        obj = DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        assert obj.meals[0].meal_type is MealType.BREAKFAST
        assert obj.meals[1].meal_type is MealType.LUNCH
        assert obj.meals[2].meal_type is MealType.DINNER
        assert obj.meals[3].meal_type is MealType.SNACK

    def test_wrong_order_rejected(self):
        d = _valid_summary_data_dict()
        meals = list(d["meals"])
        meals[0], meals[1] = meals[1], meals[0]
        d["meals"] = meals
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_duplicates_rejected(self):
        d = _valid_summary_data_dict()
        meals = list(d["meals"])
        meals[1] = dict(meals[0])
        d["meals"] = meals
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_missing_meal_rejected(self):
        d = _valid_summary_data_dict()
        d["meals"] = d["meals"][:3]
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_extra_meal_rejected(self):
        d = _valid_summary_data_dict()
        meals = list(d["meals"])
        meals.append(dict(meals[0]))
        meals[4]["meal_type"] = "breakfast"
        d["meals"] = meals
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_no_silent_sorting(self):
        d = _valid_summary_data_dict()
        meals = list(d["meals"])
        meals[0], meals[2] = meals[2], meals[0]
        meals[0]["meal_type"] = "dinner"
        meals[2]["meal_type"] = "breakfast"
        d["meals"] = meals
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_nested_extras_rejected(self):
        d = _valid_summary_data_dict()
        d["totals"]["extra"] = "value"
        with pytest.raises(ValidationError):
            DailyNutritionLogSummaryData(**d)

    def test_nested_mutation_rejected(self):
        obj = DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        with pytest.raises(ValidationError):
            obj.meals[0].entry_count = 5

    def test_from_domain_correct_type_required(self):
        with pytest.raises(TypeError, match="DailyNutritionLogSummary"):
            DailyNutritionLogSummaryData.from_domain("not summary")  # type: ignore[arg-type]

    def test_from_domain_exact_entry_count(self):
        summary = _valid_log_summary()
        data = DailyNutritionLogSummaryData.from_domain(summary)
        assert data.entry_count == summary.entry_count

    def test_from_domain_exact_overall_totals(self):
        summary = _valid_log_summary()
        data = DailyNutritionLogSummaryData.from_domain(summary)
        assert data.totals.calories_kcal == summary.totals.calories_kcal
        assert data.totals.protein_g == summary.totals.protein_g
        assert data.totals.carbohydrate_g == summary.totals.carbohydrate_g
        assert data.totals.fat_g == summary.totals.fat_g

    def test_from_domain_uses_totals_from_domain(self):
        summary = _valid_log_summary()
        data = DailyNutritionLogSummaryData.from_domain(summary)
        assert isinstance(data.totals, DailyNutritionTotalsData)

    def test_from_domain_uses_meal_from_domain(self):
        summary = _valid_log_summary()
        data = DailyNutritionLogSummaryData.from_domain(summary)
        for meal_data in data.meals:
            assert isinstance(meal_data, MealNutritionSummaryData)

    def test_from_domain_preserves_meal_order(self):
        summary = _valid_log_summary()
        data = DailyNutritionLogSummaryData.from_domain(summary)
        for i, mt in enumerate(MEAL_TYPE_ORDER):
            assert data.meals[i].meal_type is mt

    def test_from_domain_returns_tuple(self):
        summary = _valid_log_summary()
        data = DailyNutritionLogSummaryData.from_domain(summary)
        assert isinstance(data.meals, tuple)

    def test_from_domain_no_mutation(self):
        summary = _valid_log_summary()
        DailyNutritionLogSummaryData.from_domain(summary)
        assert summary.entry_count == 4

    def test_from_domain_deterministic(self):
        summary = _valid_log_summary()
        d1 = DailyNutritionLogSummaryData.from_domain(summary)
        d2 = DailyNutritionLogSummaryData.from_domain(summary)
        assert d1 == d2


# ===========================================================================
# 7. DailyNutritionLogSuccessResponse
# ===========================================================================


class TestDailyNutritionLogSuccessResponse:
    def test_exact_field_set(self):
        fields = set(DailyNutritionLogSuccessResponse.model_fields)
        expected = {"success", "message", "data"}
        assert fields == expected

    def test_success_defaults_true(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        assert obj.success is True

    def test_success_true_accepted(self):
        obj = DailyNutritionLogSuccessResponse(
            success=True,
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict()),
        )
        assert obj.success is True

    def test_success_false_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionLogSuccessResponse(
                success=False,
                data=DailyNutritionLogSummaryData(**_valid_summary_data_dict()),
            )

    def test_default_message_exact(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        assert obj.message == "Daily nutrition log summarized successfully."

    def test_data_required(self):
        with pytest.raises(ValidationError):
            DailyNutritionLogSuccessResponse()

    def test_null_data_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionLogSuccessResponse(
                data=None,  # type: ignore[arg-type]
            )

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            DailyNutritionLogSuccessResponse(
                data=DailyNutritionLogSummaryData(**_valid_summary_data_dict()),
                extra_field="value",  # type: ignore[call-arg]
            )

    def test_model_dump_result(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        dumped = obj.model_dump()
        assert dumped["success"] is True
        assert dumped["message"] == "Daily nutrition log summarized successfully."
        assert "data" in dumped
        assert "extra_field" not in dumped

    def test_model_dump_json_result(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        json_str = obj.model_dump_json()
        assert '"success": true' in json_str or '"success":true' in json_str.replace(" ", "")

    def test_decimal_serialization_behavior(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        dumped = obj.model_dump()
        assert isinstance(dumped["data"]["totals"]["calories_kcal"], Decimal)

    def test_enum_serialization_behavior(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        dumped = obj.model_dump()
        assert dumped["data"]["meals"][0]["meal_type"] == "breakfast"

    def test_nested_order_preserved(self):
        obj = DailyNutritionLogSuccessResponse(
            data=DailyNutritionLogSummaryData(**_valid_summary_data_dict())
        )
        dumped = obj.model_dump()
        meals = dumped["data"]["meals"]
        assert meals[0]["meal_type"] == "breakfast"
        assert meals[1]["meal_type"] == "lunch"
        assert meals[2]["meal_type"] == "dinner"
        assert meals[3]["meal_type"] == "snack"


# ===========================================================================
# 8. Architecture — no prohibited dependencies
# ===========================================================================


class TestArchitectureNoProhibitedImports:
    def test_no_fastapi_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "fastapi" not in source.lower()

    def test_no_starlette_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "starlette" not in source.lower()

    def test_no_sqlalchemy_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "sqlalchemy" not in source.lower()

    def test_no_alembic_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "alembic" not in source.lower()

    def test_no_database_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "session" not in source.lower()
        assert "engine" not in source.lower()

    def test_no_repository_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "repository" not in source.lower()

    def test_no_service_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "service" not in source.lower()

    def test_no_api_router_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "router" not in source.lower()

    def test_no_settings_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "settings" not in source.lower()

    def test_no_environment_access(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "environ" not in source

    def test_no_network_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "http" not in source.lower()
        assert "urllib" not in source.lower()
        assert "requests" not in source.lower()

    def test_no_usda_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "usda" not in source.lower()

    def test_no_groq_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "groq" not in source.lower()

    def test_no_openai_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "openai" not in source.lower()

    def test_no_llm_import(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "langchain" not in source.lower()
        assert "gemini" not in source.lower()

    def test_no_system_clock(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "datetime.now" not in source
        assert "datetime.utcnow" not in source
        assert "date.today" not in source
        assert "from time import" not in source

    def test_no_random(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "random" not in source

    def test_no_uuid_generation(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "uuid4" not in source
        assert "uuid1" not in source

    def test_no_aggregation_implementation(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "sum(" not in source.replace("_", "")


# ===========================================================================
# 9. Boundary — domain/schema dependency direction
# ===========================================================================


class TestBoundaryDependencyDirection:
    def test_domain_module_unmodified_during_schema_creation(self):
        import app.core.nutrition_logs as mod

        assert hasattr(mod, "MealType")
        assert hasattr(mod, "NutritionLogEntry")
        assert hasattr(mod, "DailyNutritionTotals")
        assert hasattr(mod, "MealNutritionSummary")
        assert hasattr(mod, "DailyNutritionLogSummary")
        assert hasattr(mod, "calculate_daily_nutrition_totals")
        assert hasattr(mod, "summarize_daily_nutrition_log")

    def test_domain_module_has_no_pydantic(self):
        import app.core.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "pydantic" not in source.lower()

    def test_schema_imports_domain(self):
        import app.schemas.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "from app.core.nutrition_logs import" in source

    def test_domain_does_not_import_schema(self):
        import app.core.nutrition_logs as dom

        source = inspect.getsource(dom)
        assert "app.schemas" not in source

    def test_no_circular_dependency(self):
        import app.schemas.nutrition_logs

        assert app.schemas.nutrition_logs is not None

    def test_orm_model_added_as_phase_4f_3(self):
        import app.models

        assert hasattr(app.models, "NutritionLog"), (
            "NutritionLog ORM model must exist in Phase 4F-3"
        )
        assert not hasattr(app.models, "NutritionLogEntry"), (
            "NutritionLogEntry is a domain dataclass, not an ORM model"
        )
        assert not hasattr(app.models, "DailyNutritionLog"), (
            "DailyNutritionLog should not exist as an ORM model"
        )
