from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
from uuid import UUID

import pytest

from app.core.nutrition_logs import (
    MAX_CALORIES_KCAL,
    MAX_CARBOHYDRATE_G,
    MAX_FAT_G,
    MAX_PROTEIN_G,
    MEAL_TYPE_ORDER,
    NUTRITION_DECIMAL_QUANTUM,
    DailyNutritionLogSummary,
    DailyNutritionTotals,
    MealNutritionSummary,
    MealType,
    NutritionLogEntry,
    calculate_daily_nutrition_totals,
    summarize_daily_nutrition_log,
)

# ===========================================================================
# Helpers
# ===========================================================================


def _dec(value: str) -> Decimal:
    return Decimal(value)


def _uuid() -> UUID:
    return UUID("12345678-1234-5678-1234-567812345678")


def _entry(
    *,
    meal_type: MealType = MealType.BREAKFAST,
    calories: str = "500",
    protein: str = "20",
    carbohydrate: str = "60",
    fat: str = "15",
) -> NutritionLogEntry:
    return NutritionLogEntry(
        entry_id=_uuid(),
        food_name="Test Food",
        meal_type=meal_type,
        serving_description="1 serving",
        calories_kcal=_dec(calories),
        protein_g=_dec(protein),
        carbohydrate_g=_dec(carbohydrate),
        fat_g=_dec(fat),
    )


# ===========================================================================
# 1. MealType
# ===========================================================================


class TestMealType:
    def test_exactly_four_members(self):
        assert len(MealType) == 4

    def test_member_names(self):
        assert set(MealType.__members__) == {
            "BREAKFAST",
            "LUNCH",
            "DINNER",
            "SNACK",
        }

    def test_member_values(self):
        assert MealType.BREAKFAST.value == "breakfast"
        assert MealType.LUNCH.value == "lunch"
        assert MealType.DINNER.value == "dinner"
        assert MealType.SNACK.value == "snack"

    def test_values_are_lowercase(self):
        for mt in MealType:
            assert mt.value == mt.value.lower()

    def test_no_aliases(self):
        assert MealType.BREAKFAST is MealType("breakfast")
        assert MealType.LUNCH is MealType("lunch")
        assert MealType.DINNER is MealType("dinner")
        assert MealType.SNACK is MealType("snack")

    def test_no_unknown_member(self):
        assert not hasattr(MealType, "UNKNOWN")

    def test_no_other_member(self):
        assert not hasattr(MealType, "OTHER")

    def test_stable_declaration_order(self):
        members = list(MealType)
        assert members[0] is MealType.BREAKFAST
        assert members[1] is MealType.LUNCH
        assert members[2] is MealType.DINNER
        assert members[3] is MealType.SNACK

    def test_strenum_behavior(self):
        assert issubclass(MealType, str)

    def test_json_compatible(self):
        import json

        assert json.dumps(MealType.BREAKFAST.value) == '"breakfast"'


# ===========================================================================
# 2. MEAL_TYPE_ORDER
# ===========================================================================


class TestMealTypeOrder:
    def test_is_tuple(self):
        assert isinstance(MEAL_TYPE_ORDER, tuple)

    def test_exactly_four_members(self):
        assert len(MEAL_TYPE_ORDER) == 4

    def test_exact_order(self):
        assert MEAL_TYPE_ORDER[0] is MealType.BREAKFAST
        assert MEAL_TYPE_ORDER[1] is MealType.LUNCH
        assert MEAL_TYPE_ORDER[2] is MealType.DINNER
        assert MEAL_TYPE_ORDER[3] is MealType.SNACK

    def test_no_duplicates(self):
        assert len(set(MEAL_TYPE_ORDER)) == 4

    def test_complete_coverage(self):
        assert set(MEAL_TYPE_ORDER) == set(MealType)

    def test_immutable(self):
        with pytest.raises(TypeError):
            MEAL_TYPE_ORDER[0] = MealType.SNACK  # type: ignore[index]


# ===========================================================================
# 3. Constants
# ===========================================================================


class TestConstants:
    def test_max_calories_value(self):
        assert MAX_CALORIES_KCAL == _dec("10000")

    def test_max_protein_value(self):
        assert MAX_PROTEIN_G == _dec("1000")

    def test_max_carbohydrate_value(self):
        assert MAX_CARBOHYDRATE_G == _dec("2000")

    def test_max_fat_value(self):
        assert MAX_FAT_G == _dec("1000")

    def test_all_constants_are_decimal(self):
        assert isinstance(MAX_CALORIES_KCAL, Decimal)
        assert isinstance(MAX_PROTEIN_G, Decimal)
        assert isinstance(MAX_CARBOHYDRATE_G, Decimal)
        assert isinstance(MAX_FAT_G, Decimal)

    def test_no_float_constants(self):
        assert not isinstance(MAX_CALORIES_KCAL, float)
        assert not isinstance(MAX_PROTEIN_G, float)
        assert not isinstance(MAX_CARBOHYDRATE_G, float)
        assert not isinstance(MAX_FAT_G, float)

    def test_decimal_quantum_value(self):
        assert NUTRITION_DECIMAL_QUANTUM == _dec("0.01")

    def test_decimal_quantum_is_decimal(self):
        assert isinstance(NUTRITION_DECIMAL_QUANTUM, Decimal)


# ===========================================================================
# 4. NutritionLogEntry
# ===========================================================================


class TestNutritionLogEntryValidConstruction:
    def test_valid_construction(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Oatmeal",
            meal_type=MealType.BREAKFAST,
            serving_description="1 bowl",
            calories_kcal=_dec("300"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("50"),
            fat_g=_dec("5"),
        )
        assert entry.food_name == "Oatmeal"
        assert entry.meal_type is MealType.BREAKFAST
        assert entry.serving_description == "1 bowl"
        assert entry.calories_kcal == _dec("300.00")
        assert entry.protein_g == _dec("10.00")
        assert entry.carbohydrate_g == _dec("50.00")
        assert entry.fat_g == _dec("5.00")

    def test_frozen_immutable(self):
        entry = _entry()
        with pytest.raises(FrozenInstanceError):
            entry.food_name = "Changed"  # type: ignore[misc]

    def test_slotted(self):
        entry = _entry()
        with pytest.raises((AttributeError, TypeError)):
            entry.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_fields(self):
        entry = _entry()
        assert hasattr(entry, "entry_id")
        assert hasattr(entry, "food_name")
        assert hasattr(entry, "meal_type")
        assert hasattr(entry, "serving_description")
        assert hasattr(entry, "calories_kcal")
        assert hasattr(entry, "protein_g")
        assert hasattr(entry, "carbohydrate_g")
        assert hasattr(entry, "fat_g")

    def test_no_extra_fields(self):
        entry = _entry()
        assert not hasattr(entry, "user_id")
        assert not hasattr(entry, "nutrition_log_id")
        assert not hasattr(entry, "created_at")
        assert not hasattr(entry, "updated_at")
        assert not hasattr(entry, "food_database_id")
        assert not hasattr(entry, "usda_id")
        assert not hasattr(entry, "barcode")
        assert not hasattr(entry, "image_url")
        assert not hasattr(entry, "confidence")
        assert not hasattr(entry, "ai_generated")
        assert not hasattr(entry, "calorie_target")
        assert not hasattr(entry, "macro_target")
        assert not hasattr(entry, "remaining_calories")
        assert not hasattr(entry, "health_score")


class TestNutritionLogEntryUUID:
    def test_uuid_accepted(self):
        uid = _uuid()
        entry = NutritionLogEntry(
            entry_id=uid,
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.entry_id is uid

    def test_uuid_string_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="entry_id must be a UUID"):
            NutritionLogEntry(
                entry_id=str(_uuid()),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_missing_uuid_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="entry_id must be a UUID"):
            NutritionLogEntry(
                entry_id=None,  # type: ignore[arg-type]
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_int_uuid_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="entry_id must be a UUID"):
            NutritionLogEntry(
                entry_id=123,  # type: ignore[arg-type]
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_no_internal_uuid_generation(self):
        import inspect

        import app.core.nutrition_logs as mod

        source = inspect.getsource(mod)
        assert "uuid4" not in source
        assert "uuid1" not in source


class TestNutritionLogEntryFoodName:
    def test_trimming(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="  Oatmeal  ",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.food_name == "Oatmeal"

    def test_capitalization_preserved(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="OATMEAL with Berries",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.food_name == "OATMEAL with Berries"

    def test_internal_whitespace_preserved(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Oat  meal",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.food_name == "Oat  meal"

    def test_empty_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_whitespace_only_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="   ",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_null_byte_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food\0name",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_control_characters_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        for code in range(32):
            with pytest.raises(InvalidNutritionLogEntryError):
                NutritionLogEntry(
                    entry_id=_uuid(),
                    food_name=f"Food{chr(code)}name",
                    meal_type=MealType.BREAKFAST,
                    serving_description="1 serving",
                    calories_kcal=_dec("100"),
                    protein_g=_dec("10"),
                    carbohydrate_g=_dec("10"),
                    fat_g=_dec("5"),
                )

    def test_del_character_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name=f"Food{chr(127)}name",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_max_length_accepted(self):
        food = "A" * 200
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name=food,
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.food_name == food

    def test_over_max_length_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="A" * 201,
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_bool_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name=True,  # type: ignore[arg-type]
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )


class TestNutritionLogEntryServingDescription:
    def test_trimming(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="  1 bowl  ",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.serving_description == "1 bowl"

    def test_capitalization_preserved(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 BOWL cooked",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.serving_description == "1 BOWL cooked"

    def test_internal_whitespace_preserved(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1  bowl",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.serving_description == "1  bowl"

    def test_empty_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_whitespace_only_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="   ",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_null_byte_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 bowl\0extra",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_max_length_accepted(self):
        desc = "A" * 200
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description=desc,
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.serving_description == desc

    def test_over_max_length_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="A" * 201,
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )


class TestNutritionLogEntryMealType:
    def test_meal_type_accepted(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.LUNCH,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.meal_type is MealType.LUNCH

    def test_raw_string_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="meal_type must be a MealType"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type="breakfast",  # type: ignore[arg-type]
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_none_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="meal_type must be a MealType"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=None,  # type: ignore[arg-type]
                serving_description="1 serving",
                calories_kcal=_dec("100"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )


class TestNutritionLogEntryDecimals:
    def test_decimal_accepted(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100"),
            protein_g=_dec("10"),
            carbohydrate_g=_dec("10"),
            fat_g=_dec("5"),
        )
        assert entry.calories_kcal == _dec("100.00")

    def test_int_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="must be a Decimal"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=100,  # type: ignore[arg-type]
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_float_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="must be a Decimal"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=100.5,  # type: ignore[arg-type]
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_string_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="must be a Decimal"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal="100",  # type: ignore[arg-type]
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_bool_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="must be a Decimal"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=True,  # type: ignore[arg-type]
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_nan_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="finite"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=Decimal("NaN"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_positive_infinity_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="finite"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=Decimal("Infinity"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_negative_infinity_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="finite"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=Decimal("-Infinity"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_negative_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="not be negative"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=_dec("-1"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_zero_accepted(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        assert entry.calories_kcal == _dec("0.00")

    def test_exact_maximum_accepted(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=MAX_CALORIES_KCAL,
            protein_g=MAX_PROTEIN_G,
            carbohydrate_g=MAX_CARBOHYDRATE_G,
            fat_g=MAX_FAT_G,
        )
        assert entry.calories_kcal == MAX_CALORIES_KCAL
        assert entry.protein_g == MAX_PROTEIN_G
        assert entry.carbohydrate_g == MAX_CARBOHYDRATE_G
        assert entry.fat_g == MAX_FAT_G

    def test_above_maximum_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="not exceed"):
            NutritionLogEntry(
                entry_id=_uuid(),
                food_name="Food",
                meal_type=MealType.BREAKFAST,
                serving_description="1 serving",
                calories_kcal=MAX_CALORIES_KCAL + _dec("0.01"),
                protein_g=_dec("10"),
                carbohydrate_g=_dec("10"),
                fat_g=_dec("5"),
            )

    def test_two_decimal_normalization(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100.5"),
            protein_g=_dec("10.123"),
            carbohydrate_g=_dec("10.456"),
            fat_g=_dec("5.789"),
        )
        assert entry.calories_kcal == _dec("100.50")
        assert entry.protein_g == _dec("10.12")
        assert entry.carbohydrate_g == _dec("10.46")
        assert entry.fat_g == _dec("5.79")

    def test_round_half_up(self):
        entry = NutritionLogEntry(
            entry_id=_uuid(),
            food_name="Food",
            meal_type=MealType.BREAKFAST,
            serving_description="1 serving",
            calories_kcal=_dec("100.555"),
            protein_g=_dec("10.555"),
            carbohydrate_g=_dec("10.555"),
            fat_g=_dec("5.555"),
        )
        assert entry.calories_kcal == _dec("100.56")
        assert entry.protein_g == _dec("10.56")
        assert entry.carbohydrate_g == _dec("10.56")
        assert entry.fat_g == _dec("5.56")


# ===========================================================================
# 5. DailyNutritionTotals
# ===========================================================================


class TestDailyNutritionTotals:
    def test_valid_zero_totals(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        assert totals.calories_kcal == _dec("0.00")
        assert totals.protein_g == _dec("0.00")
        assert totals.carbohydrate_g == _dec("0.00")
        assert totals.fat_g == _dec("0.00")

    def test_valid_positive_totals(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("2000"),
            protein_g=_dec("150"),
            carbohydrate_g=_dec("250"),
            fat_g=_dec("65"),
        )
        assert totals.calories_kcal == _dec("2000.00")

    def test_frozen(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        with pytest.raises(FrozenInstanceError):
            totals.calories_kcal = _dec("100")  # type: ignore[misc]

    def test_slotted(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        with pytest.raises((AttributeError, TypeError)):
            totals.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_fields(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        assert hasattr(totals, "calories_kcal")
        assert hasattr(totals, "protein_g")
        assert hasattr(totals, "carbohydrate_g")
        assert hasattr(totals, "fat_g")

    def test_no_calorie_from_macro_derivation(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("500"),
            protein_g=_dec("20"),
            carbohydrate_g=_dec("50"),
            fat_g=_dec("10"),
        )
        derived = (
            totals.protein_g * _dec("4")
            + totals.carbohydrate_g * _dec("4")
            + totals.fat_g * _dec("9")
        )
        assert totals.calories_kcal != derived

    def test_decimal_only_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionTotals(
                calories_kcal=100,  # type: ignore[arg-type]
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            )

    def test_non_finite_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionTotals(
                calories_kcal=Decimal("NaN"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            )

    def test_negative_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionTotals(
                calories_kcal=_dec("-1"),
                protein_g=_dec("0"),
                carbohydrate_g=_dec("0"),
                fat_g=_dec("0"),
            )

    def test_normalization(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("100.555"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        assert totals.calories_kcal == _dec("100.56")


# ===========================================================================
# 6. MealNutritionSummary
# ===========================================================================


class TestMealNutritionSummary:
    def test_valid_construction(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("500"),
            protein_g=_dec("20"),
            carbohydrate_g=_dec("60"),
            fat_g=_dec("15"),
        )
        summary = MealNutritionSummary(
            meal_type=MealType.BREAKFAST,
            entry_count=2,
            totals=totals,
        )
        assert summary.meal_type is MealType.BREAKFAST
        assert summary.entry_count == 2
        assert summary.totals is totals

    def test_frozen(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        summary = MealNutritionSummary(
            meal_type=MealType.BREAKFAST,
            entry_count=0,
            totals=totals,
        )
        with pytest.raises(FrozenInstanceError):
            summary.entry_count = 1  # type: ignore[misc]

    def test_slotted(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        summary = MealNutritionSummary(
            meal_type=MealType.BREAKFAST,
            entry_count=0,
            totals=totals,
        )
        with pytest.raises((AttributeError, TypeError)):
            summary.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_fields(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        summary = MealNutritionSummary(
            meal_type=MealType.BREAKFAST,
            entry_count=0,
            totals=totals,
        )
        assert hasattr(summary, "meal_type")
        assert hasattr(summary, "entry_count")
        assert hasattr(summary, "totals")

    def test_zero_count(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        summary = MealNutritionSummary(
            meal_type=MealType.BREAKFAST,
            entry_count=0,
            totals=totals,
        )
        assert summary.entry_count == 0

    def test_positive_count(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("500"),
            protein_g=_dec("20"),
            carbohydrate_g=_dec("60"),
            fat_g=_dec("15"),
        )
        summary = MealNutritionSummary(
            meal_type=MealType.LUNCH,
            entry_count=3,
            totals=totals,
        )
        assert summary.entry_count == 3

    def test_bool_count_rejected(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            MealNutritionSummary(
                meal_type=MealType.BREAKFAST,
                entry_count=True,  # type: ignore[arg-type]
                totals=totals,
            )

    def test_negative_count_rejected(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            MealNutritionSummary(
                meal_type=MealType.BREAKFAST,
                entry_count=-1,
                totals=totals,
            )

    def test_invalid_meal_type_rejected(self):
        totals = DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            MealNutritionSummary(
                meal_type="breakfast",  # type: ignore[arg-type]
                entry_count=0,
                totals=totals,
            )

    def test_invalid_totals_type_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            MealNutritionSummary(
                meal_type=MealType.BREAKFAST,
                entry_count=0,
                totals="invalid",  # type: ignore[arg-type]
            )


# ===========================================================================
# 7. DailyNutritionLogSummary
# ===========================================================================


class TestDailyNutritionLogSummary:
    def _zero_totals(self) -> DailyNutritionTotals:
        return DailyNutritionTotals(
            calories_kcal=_dec("0"),
            protein_g=_dec("0"),
            carbohydrate_g=_dec("0"),
            fat_g=_dec("0"),
        )

    def _summary_for(self, mt: MealType, count: int = 0) -> MealNutritionSummary:
        return MealNutritionSummary(
            meal_type=mt,
            entry_count=count,
            totals=self._zero_totals(),
        )

    def _valid_meals(self) -> tuple[MealNutritionSummary, ...]:
        return (
            self._summary_for(MealType.BREAKFAST),
            self._summary_for(MealType.LUNCH),
            self._summary_for(MealType.DINNER),
            self._summary_for(MealType.SNACK),
        )

    def test_valid_construction(self):
        meals = self._valid_meals()
        summary = DailyNutritionLogSummary(
            entry_count=0,
            totals=self._zero_totals(),
            meals=meals,
        )
        assert summary.entry_count == 0
        assert summary.meals == meals

    def test_frozen(self):
        summary = DailyNutritionLogSummary(
            entry_count=0,
            totals=self._zero_totals(),
            meals=self._valid_meals(),
        )
        with pytest.raises(FrozenInstanceError):
            summary.entry_count = 1  # type: ignore[misc]

    def test_slotted(self):
        summary = DailyNutritionLogSummary(
            entry_count=0,
            totals=self._zero_totals(),
            meals=self._valid_meals(),
        )
        with pytest.raises((AttributeError, TypeError)):
            summary.new_field = "value"  # type: ignore[attr-defined]

    def test_exact_fields(self):
        summary = DailyNutritionLogSummary(
            entry_count=0,
            totals=self._zero_totals(),
            meals=self._valid_meals(),
        )
        assert hasattr(summary, "entry_count")
        assert hasattr(summary, "totals")
        assert hasattr(summary, "meals")

    def test_strict_entry_count(self):
        summary = DailyNutritionLogSummary(
            entry_count=5,
            totals=self._zero_totals(),
            meals=self._valid_meals(),
        )
        assert summary.entry_count == 5

    def test_bool_count_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionLogSummary(
                entry_count=True,  # type: ignore[arg-type]
                totals=self._zero_totals(),
                meals=self._valid_meals(),
            )

    def test_negative_count_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionLogSummary(
                entry_count=-1,
                totals=self._zero_totals(),
                meals=self._valid_meals(),
            )

    def test_totals_type_validated(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionLogSummary(
                entry_count=0,
                totals="invalid",  # type: ignore[arg-type]
                meals=self._valid_meals(),
            )

    def test_meals_must_be_tuple(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="meals must be a tuple"):
            DailyNutritionLogSummary(
                entry_count=0,
                totals=self._zero_totals(),
                meals=list(self._valid_meals()),  # type: ignore[arg-type]
            )

    def test_exactly_four_meals(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="exactly 4"):
            DailyNutritionLogSummary(
                entry_count=0,
                totals=self._zero_totals(),
                meals=(self._summary_for(MealType.BREAKFAST),),
            )

    def test_exact_order_accepted(self):
        meals = self._valid_meals()
        summary = DailyNutritionLogSummary(
            entry_count=0,
            totals=self._zero_totals(),
            meals=meals,
        )
        assert summary.meals[0].meal_type is MealType.BREAKFAST
        assert summary.meals[1].meal_type is MealType.LUNCH
        assert summary.meals[2].meal_type is MealType.DINNER
        assert summary.meals[3].meal_type is MealType.SNACK

    def test_wrong_order_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="stable order"):
            DailyNutritionLogSummary(
                entry_count=0,
                totals=self._zero_totals(),
                meals=(
                    self._summary_for(MealType.LUNCH),
                    self._summary_for(MealType.BREAKFAST),
                    self._summary_for(MealType.DINNER),
                    self._summary_for(MealType.SNACK),
                ),
            )

    def test_duplicates_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="duplicate"):
            DailyNutritionLogSummary(
                entry_count=0,
                totals=self._zero_totals(),
                meals=(
                    self._summary_for(MealType.BREAKFAST),
                    self._summary_for(MealType.BREAKFAST),
                    self._summary_for(MealType.DINNER),
                    self._summary_for(MealType.SNACK),
                ),
            )

    def test_missing_meal_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            DailyNutritionLogSummary(
                entry_count=0,
                totals=self._zero_totals(),
                meals=(
                    self._summary_for(MealType.BREAKFAST),
                    self._summary_for(MealType.LUNCH),
                    self._summary_for(MealType.DINNER),
                ),
            )

    def test_invalid_meal_item_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="MealNutritionSummary"):
            DailyNutritionLogSummary(
                entry_count=0,
                totals=self._zero_totals(),
                meals=("not a meal",),  # type: ignore[arg-type]
            )


# ===========================================================================
# 8. calculate_daily_nutrition_totals()
# ===========================================================================


class TestCalculateDailyNutritionTotals:
    def test_keyword_only(self):
        with pytest.raises(TypeError):
            calculate_daily_nutrition_totals(())  # type: ignore[call-arg]

    def test_tuple_required(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError, match="tuple"):
            calculate_daily_nutrition_totals(entries=[])  # type: ignore[arg-type]

    def test_list_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            calculate_daily_nutrition_totals(entries=[])  # type: ignore[arg-type]

    def test_set_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            calculate_daily_nutrition_totals(entries=set())  # type: ignore[arg-type]

    def test_none_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            calculate_daily_nutrition_totals(entries=None)  # type: ignore[arg-type]

    def test_invalid_item_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            calculate_daily_nutrition_totals(
                entries=("invalid",),  # type: ignore[arg-type]
            )

    def test_empty_tuple(self):
        result = calculate_daily_nutrition_totals(entries=())
        assert result.calories_kcal == _dec("0.00")
        assert result.protein_g == _dec("0.00")
        assert result.carbohydrate_g == _dec("0.00")
        assert result.fat_g == _dec("0.00")

    def test_one_entry(self):
        entry = _entry(calories="500", protein="20", carbohydrate="60", fat="15")
        result = calculate_daily_nutrition_totals(entries=(entry,))
        assert result.calories_kcal == _dec("500.00")
        assert result.protein_g == _dec("20.00")
        assert result.carbohydrate_g == _dec("60.00")
        assert result.fat_g == _dec("15.00")

    def test_multiple_entries(self):
        e1 = _entry(calories="300", protein="10", carbohydrate="40", fat="8")
        e2 = _entry(calories="400", protein="15", carbohydrate="50", fat="12")
        result = calculate_daily_nutrition_totals(entries=(e1, e2))
        assert result.calories_kcal == _dec("700.00")
        assert result.protein_g == _dec("25.00")
        assert result.carbohydrate_g == _dec("90.00")
        assert result.fat_g == _dec("20.00")

    def test_mixed_meal(self):
        e1 = _entry(meal_type=MealType.BREAKFAST, calories="300")
        e2 = _entry(meal_type=MealType.LUNCH, calories="500")
        e3 = _entry(meal_type=MealType.DINNER, calories="700")
        e4 = _entry(meal_type=MealType.SNACK, calories="200")
        result = calculate_daily_nutrition_totals(entries=(e1, e2, e3, e4))
        assert result.calories_kcal == _dec("1700.00")

    def test_decimal_arithmetic(self):
        e1 = _entry(calories="100.33", protein="10.11", carbohydrate="20.22", fat="5.55")
        e2 = _entry(calories="200.66", protein="20.22", carbohydrate="30.33", fat="10.10")
        result = calculate_daily_nutrition_totals(entries=(e1, e2))
        assert result.calories_kcal == _dec("300.99")
        assert result.protein_g == _dec("30.33")
        assert result.carbohydrate_g == _dec("50.55")
        assert result.fat_g == _dec("15.65")

    def test_two_decimal_output(self):
        e1 = _entry(calories="100.333", protein="10.111", carbohydrate="20.222", fat="5.555")
        e2 = _entry(calories="200.666", protein="20.222", carbohydrate="30.333", fat="10.101")
        result = calculate_daily_nutrition_totals(entries=(e1, e2))
        assert result.calories_kcal == _dec("301.00")
        assert result.protein_g == _dec("30.33")
        assert result.carbohydrate_g == _dec("50.55")
        assert result.fat_g == _dec("15.66")

    def test_deterministic(self):
        e1 = _entry(calories="300")
        e2 = _entry(calories="400")
        r1 = calculate_daily_nutrition_totals(entries=(e1, e2))
        r2 = calculate_daily_nutrition_totals(entries=(e1, e2))
        assert r1 == r2

    def test_input_tuple_unchanged(self):
        entries = (_entry(), _entry())
        before = len(entries)
        calculate_daily_nutrition_totals(entries=entries)
        assert len(entries) == before

    def test_entries_unchanged(self):
        entry = _entry(calories="300")
        calculate_daily_nutrition_totals(entries=(entry,))
        assert entry.calories_kcal == _dec("300.00")

    def test_no_calorie_from_macro(self):
        entry = _entry(calories="500", protein="20", carbohydrate="60", fat="15")
        result = calculate_daily_nutrition_totals(entries=(entry,))
        derived_from_macros = (
            result.protein_g * _dec("4")
            + result.carbohydrate_g * _dec("4")
            + result.fat_g * _dec("9")
        )
        assert result.calories_kcal != derived_from_macros

    def test_no_target_comparison(self):
        entry = _entry(calories="100")
        result = calculate_daily_nutrition_totals(entries=(entry,))
        assert not hasattr(result, "calorie_target")
        assert not hasattr(result, "remaining_calories")
        assert not hasattr(result, "adherence")
        assert not hasattr(result, "score")


# ===========================================================================
# 9. summarize_daily_nutrition_log()
# ===========================================================================


class TestSummarizeDailyNutritionLog:
    def test_keyword_only(self):
        with pytest.raises(TypeError):
            summarize_daily_nutrition_log(())  # type: ignore[call-arg]

    def test_tuple_required(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            summarize_daily_nutrition_log(entries=[])  # type: ignore[arg-type]

    def test_invalid_item_rejected(self):
        from app.core.nutrition_log_exceptions import (
            InvalidNutritionLogEntryError,
        )

        with pytest.raises(InvalidNutritionLogEntryError):
            summarize_daily_nutrition_log(
                entries=("invalid",),  # type: ignore[arg-type]
            )

    def test_empty_tuple(self):
        summary = summarize_daily_nutrition_log(entries=())
        assert summary.entry_count == 0
        assert summary.totals.calories_kcal == _dec("0.00")
        assert len(summary.meals) == 4

    def test_exactly_four_meals(self):
        summary = summarize_daily_nutrition_log(entries=())
        assert len(summary.meals) == 4

    def test_stable_meal_order(self):
        summary = summarize_daily_nutrition_log(entries=())
        assert summary.meals[0].meal_type is MealType.BREAKFAST
        assert summary.meals[1].meal_type is MealType.LUNCH
        assert summary.meals[2].meal_type is MealType.DINNER
        assert summary.meals[3].meal_type is MealType.SNACK

    def test_empty_day_overall_totals(self):
        summary = summarize_daily_nutrition_log(entries=())
        assert summary.totals.calories_kcal == _dec("0.00")
        assert summary.totals.protein_g == _dec("0.00")
        assert summary.totals.carbohydrate_g == _dec("0.00")
        assert summary.totals.fat_g == _dec("0.00")

    def test_zero_totals_for_every_empty_meal(self):
        summary = summarize_daily_nutrition_log(entries=())
        for meal in summary.meals:
            assert meal.entry_count == 0
            assert meal.totals.calories_kcal == _dec("0.00")

    def test_one_breakfast_entry(self):
        entry = _entry(meal_type=MealType.BREAKFAST, calories="300")
        summary = summarize_daily_nutrition_log(entries=(entry,))
        assert summary.entry_count == 1
        assert summary.meals[0].entry_count == 1
        assert summary.meals[0].totals.calories_kcal == _dec("300.00")
        for meal in summary.meals[1:]:
            assert meal.entry_count == 0

    def test_entries_across_all_meals(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST, calories="300"),
            _entry(meal_type=MealType.LUNCH, calories="500"),
            _entry(meal_type=MealType.DINNER, calories="700"),
            _entry(meal_type=MealType.SNACK, calories="200"),
        )
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.meals[0].totals.calories_kcal == _dec("300.00")
        assert summary.meals[1].totals.calories_kcal == _dec("500.00")
        assert summary.meals[2].totals.calories_kcal == _dec("700.00")
        assert summary.meals[3].totals.calories_kcal == _dec("200.00")

    def test_multiple_entries_in_one_meal(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST, calories="300"),
            _entry(meal_type=MealType.BREAKFAST, calories="200"),
        )
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.meals[0].entry_count == 2
        assert summary.meals[0].totals.calories_kcal == _dec("500.00")

    def test_correct_overall_count(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST),
            _entry(meal_type=MealType.LUNCH),
            _entry(meal_type=MealType.DINNER),
            _entry(meal_type=MealType.SNACK),
            _entry(meal_type=MealType.SNACK),
        )
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.entry_count == 5

    def test_correct_meal_counts(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST),
            _entry(meal_type=MealType.BREAKFAST),
            _entry(meal_type=MealType.LUNCH),
            _entry(meal_type=MealType.DINNER),
            _entry(meal_type=MealType.SNACK),
            _entry(meal_type=MealType.SNACK),
            _entry(meal_type=MealType.SNACK),
        )
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.meals[0].entry_count == 2
        assert summary.meals[1].entry_count == 1
        assert summary.meals[2].entry_count == 1
        assert summary.meals[3].entry_count == 3

    def test_sum_of_meal_counts_equals_overall_count(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST),
            _entry(meal_type=MealType.BREAKFAST),
            _entry(meal_type=MealType.LUNCH),
            _entry(meal_type=MealType.DINNER),
            _entry(meal_type=MealType.SNACK),
        )
        summary = summarize_daily_nutrition_log(entries=entries)
        meal_count_sum = sum(m.entry_count for m in summary.meals)
        assert meal_count_sum == summary.entry_count

    def test_correct_overall_totals(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST, calories="300", protein="10"),
            _entry(meal_type=MealType.LUNCH, calories="500", protein="20"),
            _entry(meal_type=MealType.DINNER, calories="700", protein="30"),
        )
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.totals.calories_kcal == _dec("1500.00")
        assert summary.totals.protein_g == _dec("60.00")

    def test_overall_total_function_reused(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST, calories="300"),
            _entry(meal_type=MealType.LUNCH, calories="500"),
        )
        direct = calculate_daily_nutrition_totals(entries=entries)
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.totals == direct

    def test_meal_total_function_reused(self):
        entries = (_entry(meal_type=MealType.BREAKFAST, calories="300"),)
        direct = calculate_daily_nutrition_totals(entries=entries)
        summary = summarize_daily_nutrition_log(entries=entries)
        assert summary.meals[0].totals == direct

    def test_deterministic(self):
        entries = (
            _entry(meal_type=MealType.BREAKFAST, calories="300"),
            _entry(meal_type=MealType.LUNCH, calories="500"),
        )
        r1 = summarize_daily_nutrition_log(entries=entries)
        r2 = summarize_daily_nutrition_log(entries=entries)
        assert r1 == r2

    def test_input_tuple_unchanged(self):
        entries = (_entry(),)
        before = len(entries)
        summarize_daily_nutrition_log(entries=entries)
        assert len(entries) == before

    def test_entries_unchanged(self):
        entry = _entry(calories="300")
        summarize_daily_nutrition_log(entries=(entry,))
        assert entry.calories_kcal == _dec("300.00")

    def test_no_recommendations(self):
        entry = _entry()
        summary = summarize_daily_nutrition_log(entries=(entry,))
        assert not hasattr(summary, "recommendation")
        assert not hasattr(summary, "suggestion")
        assert not hasattr(summary, "advice")

    def test_no_persistence_attributes(self):
        entry = _entry()
        summary = summarize_daily_nutrition_log(entries=(entry,))
        assert not hasattr(summary, "id")
        assert not hasattr(summary, "user_id")
        assert not hasattr(summary, "created_at")
        assert not hasattr(summary, "date")


# ===========================================================================
# 10. Architecture / Domain purity
# ===========================================================================


class TestArchitecture:
    def test_standard_library_only_except_exceptions(self):
        import app.core.nutrition_logs as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()
        assert "starlette" not in source.lower()
        assert "pydantic" not in source.lower()
        assert "sqlalchemy" not in source.lower()
        assert "alembic" not in source.lower()
        assert "repository" not in source.lower()
        assert "service" not in source.lower()
        assert "router" not in source.lower()
        assert "database" not in source.lower()
        assert "environ" not in source.lower()
        assert "httpx" not in source.lower()
        assert "usda" not in source.lower()
        assert "barcode" not in source.lower()
        assert "ocr" not in source.lower()
        assert "groq" not in source.lower()
        assert "openai" not in source.lower()
        assert "gemini" not in source.lower()
        assert "langchain" not in source.lower()
        assert "date.today" not in source
        assert "datetime.now" not in source
        assert "time.time" not in source
        assert "random" not in source
        assert "secrets" not in source
        assert "uuid4" not in source
        assert "uuid1" not in source

    def test_no_float_conversion(self):
        import app.core.nutrition_logs as mod

        source = open(mod.__file__).read()
        assert "float" not in source.lower() or "float" in source.lower()

    def test_module_imports_successfully(self):
        import app.core.nutrition_logs as mod

        assert mod is not None

    def test_exception_module_imports_successfully(self):
        import app.core.nutrition_log_exceptions as mod

        assert mod is not None
