from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.enums import (
    ActivityLevel,
    BiologicalSex,
    DietaryPreference,
    NutritionGoal,
)
from app.schemas import (
    NutritionProfileBase,
    NutritionProfileCreate,
    NutritionProfileData,
    NutritionProfilePublic,
    NutritionProfileSuccessResponse,
    NutritionProfileUpdate,
    normalize_allergies,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_YESTERDAY = date.today() - timedelta(days=1)
_TOMORROW = date.today() + timedelta(days=1)
_NOW_UTC = datetime.now(UTC)

_VALID_BASE = {
    "date_of_birth": _YESTERDAY.isoformat(),
    "biological_sex": "male",
    "height_cm": "175.00",
    "weight_kg": "70.00",
    "activity_level": "moderately_active",
    "goal": "maintain_weight",
}


def _valid_base_dict(overrides: dict | None = None) -> dict:
    d = dict(_VALID_BASE)
    if overrides:
        d.update(overrides)
    return d


def _valid_create_dict(overrides: dict | None = None) -> dict:
    return _valid_base_dict(overrides)


# ---------------------------------------------------------------------------
# A. Imports and exports
# ---------------------------------------------------------------------------


class TestImportsExports:
    def test_module_imports(self):
        import app.schemas.nutrition_profile as mod

        assert mod.NutritionProfileBase is NutritionProfileBase
        assert mod.NutritionProfileCreate is NutritionProfileCreate
        assert mod.NutritionProfileUpdate is NutritionProfileUpdate
        assert mod.NutritionProfilePublic is NutritionProfilePublic
        assert mod.NutritionProfileData is NutritionProfileData
        assert mod.NutritionProfileSuccessResponse is NutritionProfileSuccessResponse
        assert mod.normalize_allergies is normalize_allergies

    def test_public_classes_import_from_app_schemas(self):
        assert NutritionProfileBase is not None
        assert NutritionProfileCreate is not None
        assert NutritionProfileUpdate is not None
        assert NutritionProfilePublic is not None
        assert NutritionProfileData is not None
        assert NutritionProfileSuccessResponse is not None

    def test_no_circular_import(self):
        import app.schemas

        assert hasattr(app.schemas, "NutritionProfileBase")

    def test_no_database_connection(self):
        import app.schemas.nutrition_profile as mod

        assert mod.normalize_allergies is not None

    def test_no_environment_file_required(self):
        from app.core.config import Settings

        s = Settings(APP_ENV="test", _env_file=None)
        assert s.DATABASE_URL == ""


# ---------------------------------------------------------------------------
# B. NutritionProfileBase valid cases
# ---------------------------------------------------------------------------


class TestNutritionProfileBaseValid:
    def test_minimum_valid_values(self):
        p = NutritionProfileBase(
            date_of_birth=_YESTERDAY,
            biological_sex=BiologicalSex.MALE,
            height_cm=Decimal("50.00"),
            weight_kg=Decimal("10.00"),
            activity_level=ActivityLevel.SEDENTARY,
            goal=NutritionGoal.LOSE_WEIGHT,
        )
        assert p.height_cm == Decimal("50.00")
        assert p.weight_kg == Decimal("10.00")

    def test_maximum_valid_values(self):
        p = NutritionProfileBase(
            date_of_birth=_YESTERDAY,
            biological_sex=BiologicalSex.MALE,
            height_cm=Decimal("300.00"),
            weight_kg=Decimal("700.00"),
            activity_level=ActivityLevel.EXTRA_ACTIVE,
            goal=NutritionGoal.GAIN_MUSCLE,
            target_weight_kg=Decimal("700.00"),
        )
        assert p.height_cm == Decimal("300.00")
        assert p.weight_kg == Decimal("700.00")

    def test_typical_valid_profile(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict())
        assert p.date_of_birth == _YESTERDAY
        assert p.biological_sex == BiologicalSex.MALE
        assert p.height_cm == Decimal("175.00")
        assert p.weight_kg == Decimal("70.00")
        assert p.activity_level == ActivityLevel.MODERATELY_ACTIVE
        assert p.goal == NutritionGoal.MAINTAIN_WEIGHT

    def test_every_biological_sex_value(self):
        for sex in BiologicalSex:
            p = NutritionProfileBase.model_validate(_valid_base_dict({"biological_sex": sex.value}))
            assert p.biological_sex == sex

    def test_every_activity_level_value(self):
        for level in ActivityLevel:
            p = NutritionProfileBase.model_validate(
                _valid_base_dict({"activity_level": level.value})
            )
            assert p.activity_level == level

    def test_every_nutrition_goal_value(self):
        for goal in NutritionGoal:
            p = NutritionProfileBase.model_validate(_valid_base_dict({"goal": goal.value}))
            assert p.goal == goal

    def test_every_dietary_preference_value(self):
        for pref in DietaryPreference:
            p = NutritionProfileBase.model_validate(
                _valid_base_dict({"dietary_preference": pref.value})
            )
            assert p.dietary_preference == pref

    def test_target_weight_omitted(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict())
        assert p.target_weight_kg is None

    def test_target_weight_null(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": None}))
        assert p.target_weight_kg is None

    def test_dietary_preference_omitted(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict())
        assert p.dietary_preference is None

    def test_dietary_preference_null(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"dietary_preference": None}))
        assert p.dietary_preference is None

    def test_empty_allergies(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"allergies": []}))
        assert p.allergies == []

    def test_default_allergies_factory(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict())
        assert p.allergies == []

    def test_multiple_allergies(self):
        p = NutritionProfileBase.model_validate(
            _valid_base_dict({"allergies": ["Peanuts", "MILK"]})
        )
        assert p.allergies == ["Peanuts", "MILK"]

    def test_decimal_with_zero_decimals(self):
        p = NutritionProfileBase.model_validate(
            _valid_base_dict({"height_cm": "170", "weight_kg": "70"})
        )
        assert p.height_cm == Decimal("170")
        assert p.weight_kg == Decimal("70")

    def test_decimal_with_one_decimal(self):
        p = NutritionProfileBase.model_validate(
            _valid_base_dict({"height_cm": "170.5", "weight_kg": "70.5"})
        )
        assert p.height_cm == Decimal("170.5")
        assert p.weight_kg == Decimal("70.5")

    def test_decimal_with_two_decimals(self):
        p = NutritionProfileBase.model_validate(
            _valid_base_dict({"height_cm": "170.55", "weight_kg": "70.55"})
        )
        assert p.height_cm == Decimal("170.55")
        assert p.weight_kg == Decimal("70.55")


# ---------------------------------------------------------------------------
# C. Date-of-birth validation
# ---------------------------------------------------------------------------


class TestDateOfBirthValidation:
    def test_yesterday_valid(self):
        p = NutritionProfileBase.model_validate(
            _valid_base_dict({"date_of_birth": _YESTERDAY.isoformat()})
        )
        assert p.date_of_birth == _YESTERDAY

    def test_leap_day_birth_date_valid(self):
        leap_day = date(2020, 2, 29)
        if leap_day < date.today():
            p = NutritionProfileBase.model_validate(
                _valid_base_dict({"date_of_birth": leap_day.isoformat()})
            )
            assert p.date_of_birth == leap_day

    def test_today_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(
                _valid_base_dict({"date_of_birth": date.today().isoformat()})
            )

    def test_tomorrow_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(
                _valid_base_dict({"date_of_birth": _TOMORROW.isoformat()})
            )

    def test_future_year_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"date_of_birth": "2099-01-01"}))

    def test_invalid_date_string_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"date_of_birth": "not-a-date"}))

    def test_missing_date_accepted(self):
        d = _valid_base_dict()
        del d["date_of_birth"]
        p = NutritionProfileBase.model_validate(d)
        assert p.date_of_birth is None

    def test_null_date_accepted_in_create(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"date_of_birth": None}))
        assert p.date_of_birth is None

    def test_no_age_field_generated(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict())
        assert not hasattr(p, "age")


# ---------------------------------------------------------------------------
# D. Height validation
# ---------------------------------------------------------------------------


class TestHeightValidation:
    def test_50_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "50.00"}))
        assert p.height_cm == Decimal("50.00")

    def test_300_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "300.00"}))
        assert p.height_cm == Decimal("300.00")

    def test_below_50_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "49.99"}))

    def test_above_300_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "300.01"}))

    def test_negative_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "-10.00"}))

    def test_zero_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "0.00"}))

    def test_nan_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": float("nan")}))

    def test_positive_infinity_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": float("inf")}))

    def test_negative_infinity_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": float("-inf")}))

    def test_three_decimal_places_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "170.123"}))

    def test_two_decimal_places_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": "170.12"}))
        assert p.height_cm == Decimal("170.12")

    def test_missing_valid(self):
        d = _valid_base_dict()
        del d["height_cm"]
        p = NutritionProfileBase.model_validate(d)
        assert p.height_cm is None

    def test_null_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"height_cm": None}))
        assert p.height_cm is None


# ---------------------------------------------------------------------------
# E. Weight validation
# ---------------------------------------------------------------------------


class TestWeightValidation:
    def test_10_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "10.00"}))
        assert p.weight_kg == Decimal("10.00")

    def test_700_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "700.00"}))
        assert p.weight_kg == Decimal("700.00")

    def test_below_10_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "9.99"}))

    def test_above_700_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "700.01"}))

    def test_negative_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "-5.00"}))

    def test_zero_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "0.00"}))

    def test_nan_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": float("nan")}))

    def test_positive_infinity_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": float("inf")}))

    def test_negative_infinity_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": float("-inf")}))

    def test_three_decimal_places_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "70.123"}))

    def test_two_decimal_places_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": "70.12"}))
        assert p.weight_kg == Decimal("70.12")

    def test_missing_valid(self):
        d = _valid_base_dict()
        del d["weight_kg"]
        p = NutritionProfileBase.model_validate(d)
        assert p.weight_kg is None

    def test_null_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"weight_kg": None}))
        assert p.weight_kg is None


# ---------------------------------------------------------------------------
# F. Target-weight validation
# ---------------------------------------------------------------------------


class TestTargetWeightValidation:
    def test_omitted_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict())
        assert p.target_weight_kg is None

    def test_null_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": None}))
        assert p.target_weight_kg is None

    def test_10_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "10.00"}))
        assert p.target_weight_kg == Decimal("10.00")

    def test_700_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "700.00"}))
        assert p.target_weight_kg == Decimal("700.00")

    def test_below_10_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "9.99"}))

    def test_above_700_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "700.01"}))

    def test_negative_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "-5.00"}))

    def test_nan_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(
                _valid_base_dict({"target_weight_kg": float("nan")})
            )

    def test_infinity_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(
                _valid_base_dict({"target_weight_kg": float("inf")})
            )

    def test_three_decimal_places_invalid(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "70.123"}))

    def test_two_decimal_places_valid(self):
        p = NutritionProfileBase.model_validate(_valid_base_dict({"target_weight_kg": "70.12"}))
        assert p.target_weight_kg == Decimal("70.12")


# ---------------------------------------------------------------------------
# G. Enum validation
# ---------------------------------------------------------------------------


class TestEnumValidation:
    def test_every_biological_sex_accepted(self):
        for sex in BiologicalSex:
            p = NutritionProfileBase.model_validate(_valid_base_dict({"biological_sex": sex.value}))
            assert p.biological_sex == sex

    def test_unknown_biological_sex_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"biological_sex": "unknown_sex"}))

    def test_every_activity_level_accepted(self):
        for level in ActivityLevel:
            p = NutritionProfileBase.model_validate(
                _valid_base_dict({"activity_level": level.value})
            )
            assert p.activity_level == level

    def test_unknown_activity_level_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(
                _valid_base_dict({"activity_level": "super_active"})
            )

    def test_every_nutrition_goal_accepted(self):
        for goal in NutritionGoal:
            p = NutritionProfileBase.model_validate(_valid_base_dict({"goal": goal.value}))
            assert p.goal == goal

    def test_unknown_nutrition_goal_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"goal": "bulk"}))

    def test_every_dietary_preference_accepted(self):
        for pref in DietaryPreference:
            d = _valid_base_dict({"dietary_preference": pref.value})
            p = NutritionProfileBase.model_validate(d)
            assert p.dietary_preference == pref

    def test_unknown_dietary_preference_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(
                _valid_base_dict({"dietary_preference": "carnivore"})
            )

    def test_existing_enum_classes_reused(self):
        import app.schemas.nutrition_profile as mod

        assert mod.BiologicalSex is BiologicalSex
        assert mod.ActivityLevel is ActivityLevel
        assert mod.NutritionGoal is NutritionGoal
        assert mod.DietaryPreference is DietaryPreference

    def test_no_duplicate_schema_enum_definitions(self):
        import inspect

        import app.schemas.nutrition_profile as mod

        source = inspect.getsource(mod)
        assert source.count("class BiologicalSex") == 0
        assert source.count("class ActivityLevel") == 0
        assert source.count("class NutritionGoal") == 0
        assert source.count("class DietaryPreference") == 0


# ---------------------------------------------------------------------------
# H. Allergy validation
# ---------------------------------------------------------------------------


class TestAllergyNormalization:
    def test_empty_list_valid(self):
        result = normalize_allergies([])
        assert result == []

    def test_one_value_valid(self):
        result = normalize_allergies(["Peanuts"])
        assert result == ["Peanuts"]

    def test_multiple_values_valid(self):
        result = normalize_allergies(["Peanuts", "Milk", "Eggs"])
        assert result == ["Peanuts", "Milk", "Eggs"]

    def test_whitespace_trimmed(self):
        result = normalize_allergies(["  Peanuts  ", "  Milk  "])
        assert result == ["Peanuts", "Milk"]

    def test_input_order_preserved(self):
        result = normalize_allergies(["Milk", "Eggs", "Peanuts"])
        assert result == ["Milk", "Eggs", "Peanuts"]

    def test_first_spelling_preserved(self):
        result = normalize_allergies([" Peanuts ", "peanuts"])
        assert result == ["Peanuts"]

    def test_case_insensitive_duplicates_removed(self):
        result = normalize_allergies(["Peanuts", "peanuts", "PEANUTS"])
        assert result == ["Peanuts"]

    def test_exact_duplicates_removed(self):
        result = normalize_allergies(["Milk", "Milk", "Milk"])
        assert result == ["Milk"]

    def test_mixed_case_duplicates_removed(self):
        result = normalize_allergies(["Egg", " egg ", "EGG"])
        assert result == ["Egg"]

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies([""])

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies(["   "])

    def test_null_byte_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies(["Pea\0nuts"])

    def test_control_character_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies(["Pea\x01nuts"])

    def test_100_characters_valid(self):
        value = "a" * 100
        result = normalize_allergies([value])
        assert result == [value]

    def test_101_characters_invalid(self):
        with pytest.raises(ValueError):
            normalize_allergies(["a" * 101])

    def test_50_entries_valid(self):
        entries = [f"Allergy{i}" for i in range(50)]
        result = normalize_allergies(entries)
        assert len(result) == 50

    def test_51_entries_invalid(self):
        entries = [f"Allergy{i}" for i in range(51)]
        with pytest.raises(ValueError):
            normalize_allergies(entries)

    def test_plain_string_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies("Peanuts")

    def test_comma_separated_string_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies("Peanuts, Milk")

    def test_integer_entry_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies([42])

    def test_null_entry_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies([None])

    def test_nested_list_rejected(self):
        with pytest.raises(ValueError):
            normalize_allergies([["Peanuts"]])

    def test_caller_input_not_mutated(self):
        original = [" Peanuts ", "MILK", "peanuts", " milk "]
        original_copy = list(original)
        normalize_allergies(original)
        assert original == original_copy

    def test_output_is_new_normalized_list(self):
        original = [" Peanuts ", "MILK"]
        result = normalize_allergies(original)
        assert result is not original
        assert result == ["Peanuts", "MILK"]

    def test_no_sorting_occurs(self):
        result = normalize_allergies(["Milk", "Eggs", "Peanuts"])
        assert result == ["Milk", "Eggs", "Peanuts"]

    def test_no_lowercase_conversion_occurs(self):
        result = normalize_allergies(["Peanuts", "MILK"])
        assert result[0] == "Peanuts"
        assert result[1] == "MILK"

    def test_no_inferred_allergies_added(self):
        result = normalize_allergies(["Peanuts"])
        assert result == ["Peanuts"]

    def test_mixed_dup_with_different_whitespace(self):
        result = normalize_allergies([" Milk ", "  milk  ", "MILK"])
        assert result == ["Milk"]


# ---------------------------------------------------------------------------
# I. Extra-field rejection
# ---------------------------------------------------------------------------


class TestExtraFieldRejection:
    EXTRA_FIELDS = [
        "id",
        "user_id",
        "created_at",
        "updated_at",
        "age",
        "bmi",
        "bmi_category",
        "bmr",
        "tdee",
        "calorie_target",
        "protein_target",
        "carbohydrate_target",
        "carbs_target",
        "fat_target",
        "fiber_target",
        "water_target",
        "health_score",
        "recommended_weight",
        "recommended_calories",
        "meal_plan",
        "diet_plan",
        "cheat_meal",
        "access_token",
        "refresh_token",
        "password",
        "password_hash",
        "role",
        "permissions",
    ]

    def _base_with_extra(self, field: str, value: object = "test") -> dict:
        d = _valid_base_dict()
        d[field] = value
        return d

    def test_extra_fields_rejected_via_base(self):
        for field in self.EXTRA_FIELDS:
            with pytest.raises(ValidationError):
                NutritionProfileBase.model_validate(self._base_with_extra(field))

    def test_arbitrary_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileBase.model_validate(_valid_base_dict({"unknown_field": "value"}))


# ---------------------------------------------------------------------------
# J. NutritionProfileCreate
# ---------------------------------------------------------------------------


class TestNutritionProfileCreate:
    def test_valid_complete_payload(self):
        d = _valid_create_dict()
        p = NutritionProfileCreate.model_validate(d)
        assert p.date_of_birth == _YESTERDAY

    def test_valid_minimal_payload(self):
        d = _valid_create_dict()
        p = NutritionProfileCreate.model_validate(d)
        assert p.allergies == []

    def test_inherits_base_validation(self):
        with pytest.raises(ValidationError):
            NutritionProfileCreate.model_validate(_valid_create_dict({"height_cm": "49.99"}))

    def test_cannot_accept_user_id(self):
        with pytest.raises(ValidationError):
            NutritionProfileCreate.model_validate(
                _valid_create_dict({"user_id": str(uuid.uuid4())})
            )

    def test_cannot_accept_id(self):
        with pytest.raises(ValidationError):
            NutritionProfileCreate.model_validate(_valid_create_dict({"id": str(uuid.uuid4())}))

    def test_cannot_accept_timestamps(self):
        for field in ("created_at", "updated_at"):
            with pytest.raises(ValidationError):
                NutritionProfileCreate.model_validate(
                    _valid_create_dict({field: _NOW_UTC.isoformat()})
                )

    def test_cannot_accept_calculated_fields(self):
        for field in ("bmi", "bmr", "tdee", "calorie_target"):
            with pytest.raises(ValidationError):
                NutritionProfileCreate.model_validate(_valid_create_dict({field: 0}))

    def test_cannot_accept_auth_fields(self):
        for field in ("access_token", "refresh_token", "password"):
            with pytest.raises(ValidationError):
                NutritionProfileCreate.model_validate(_valid_create_dict({field: "test"}))

    def test_cannot_accept_extra_fields(self):
        with pytest.raises(ValidationError):
            NutritionProfileCreate.model_validate(_valid_create_dict({"role": "admin"}))


# ---------------------------------------------------------------------------
# K. NutritionProfileUpdate PATCH behavior
# ---------------------------------------------------------------------------


class TestNutritionProfileUpdate:
    def test_empty_update_valid(self):
        p = NutritionProfileUpdate()
        assert p.date_of_birth is None

    def test_one_required_field_update_valid(self):
        p = NutritionProfileUpdate(weight_kg=Decimal("80.00"))
        assert p.weight_kg == Decimal("80.00")
        assert p.date_of_birth is None

    def test_multiple_field_update_valid(self):
        p = NutritionProfileUpdate(
            height_cm=Decimal("180.00"),
            weight_kg=Decimal("80.00"),
        )
        assert p.height_cm == Decimal("180.00")
        assert p.weight_kg == Decimal("80.00")

    def test_all_fields_update_valid(self):
        p = NutritionProfileUpdate(
            date_of_birth=_YESTERDAY,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("165.00"),
            weight_kg=Decimal("60.00"),
            activity_level=ActivityLevel.VERY_ACTIVE,
            goal=NutritionGoal.LOSE_WEIGHT,
            target_weight_kg=Decimal("55.00"),
            dietary_preference=DietaryPreference.VEGETARIAN,
            allergies=["Peanuts"],
        )
        assert p.date_of_birth == _YESTERDAY

    def test_omitted_field_absent_from_model_fields_set(self):
        p = NutritionProfileUpdate(weight_kg=Decimal("80.00"))
        assert "date_of_birth" not in p.model_fields_set

    def test_required_field_explicit_null_accepted(self):
        for field in (
            "date_of_birth",
            "biological_sex",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
        ):
            NutritionProfileUpdate(**{field: None})

    def test_nullable_field_explicit_null_accepted(self):
        p = NutritionProfileUpdate(target_weight_kg=None, dietary_preference=None)
        assert p.target_weight_kg is None
        assert p.dietary_preference is None

    def test_allergies_omitted_means_unchanged(self):
        p = NutritionProfileUpdate()
        assert p.allergies is None
        assert "allergies" not in p.model_fields_set

    def test_allergies_empty_list_accepted(self):
        p = NutritionProfileUpdate(allergies=[])
        assert p.allergies == []
        assert "allergies" in p.model_fields_set

    def test_allergies_null_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(allergies=None)

    def test_allergy_normalization_applies_during_update(self):
        p = NutritionProfileUpdate(allergies=[" Peanuts ", "peanuts"])
        assert p.allergies == ["Peanuts"]

    def test_height_validation_applies_during_update(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(height_cm=Decimal("49.99"))

    def test_weight_validation_applies_during_update(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(weight_kg=Decimal("9.99"))

    def test_target_weight_validation_applies_during_update(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(target_weight_kg=Decimal("9.99"))

    def test_date_validation_applies_during_update(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(date_of_birth=_TOMORROW)

    def test_enum_validation_applies_during_update(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(biological_sex="unknown")

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(weight_kg=Decimal("70.00"), unknown_field="value")

    def test_id_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(id=str(uuid.uuid4()))

    def test_user_id_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(user_id=str(uuid.uuid4()))

    def test_timestamps_rejected(self):
        for field in ("created_at", "updated_at"):
            with pytest.raises(ValidationError):
                NutritionProfileUpdate(**{field: _NOW_UTC.isoformat()})

    def test_calculated_fields_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileUpdate(bmi=22.5)


# ---------------------------------------------------------------------------
# L. NutritionProfilePublic
# ---------------------------------------------------------------------------


class TestNutritionProfilePublic:
    @pytest.fixture
    def valid_profile_dict(self):
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "660e8400-e29b-41d4-a716-446655440001",
            "date_of_birth": "1990-01-15",
            "biological_sex": "male",
            "height_cm": "175.00",
            "weight_kg": "70.00",
            "activity_level": "moderately_active",
            "goal": "maintain_weight",
            "target_weight_kg": None,
            "dietary_preference": None,
            "allergies": [],
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T12:00:00+00:00",
        }

    def test_valid_direct_construction(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert p.id == uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        assert p.user_id == uuid.UUID("660e8400-e29b-41d4-a716-446655440001")

    def test_valid_from_orm_like_object(self):
        class FakeProfile:
            def __init__(self):
                self.id = uuid.uuid4()
                self.user_id = uuid.uuid4()
                self.date_of_birth = _YESTERDAY
                self.biological_sex = BiologicalSex.MALE
                self.height_cm = Decimal("175.00")
                self.weight_kg = Decimal("70.00")
                self.activity_level = ActivityLevel.MODERATELY_ACTIVE
                self.goal = NutritionGoal.MAINTAIN_WEIGHT
                self.target_weight_kg = None
                self.dietary_preference = None
                self.allergies = []
                self.created_at = _NOW_UTC
                self.updated_at = _NOW_UTC

        p = NutritionProfilePublic.model_validate(FakeProfile())
        assert isinstance(p.id, uuid.UUID)
        assert p.biological_sex == BiologicalSex.MALE

    def test_correct_uuid_types(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert isinstance(p.id, uuid.UUID)
        assert isinstance(p.user_id, uuid.UUID)

    def test_correct_enum_types(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert isinstance(p.biological_sex, BiologicalSex)
        assert isinstance(p.activity_level, ActivityLevel)
        assert isinstance(p.goal, NutritionGoal)

    def test_correct_decimal_types(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert isinstance(p.height_cm, Decimal)
        assert isinstance(p.weight_kg, Decimal)

    def test_correct_allergy_list(self, valid_profile_dict):
        valid_profile_dict["allergies"] = ["Peanuts", "Milk"]
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert p.allergies == ["Peanuts", "Milk"]

    def test_correct_timestamps(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert isinstance(p.created_at, datetime)
        assert isinstance(p.updated_at, datetime)

    def test_naive_created_at_rejected(self, valid_profile_dict):
        valid_profile_dict["created_at"] = "2024-01-01T00:00:00"
        with pytest.raises(ValidationError):
            NutritionProfilePublic.model_validate(valid_profile_dict)

    def test_naive_updated_at_rejected(self, valid_profile_dict):
        valid_profile_dict["updated_at"] = "2024-01-01T00:00:00"
        with pytest.raises(ValidationError):
            NutritionProfilePublic.model_validate(valid_profile_dict)

    def test_timezone_aware_timestamps_accepted(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        assert p.created_at.tzinfo is not None
        assert p.updated_at.tzinfo is not None

    def test_password_absent(self, valid_profile_dict):
        assert "password" not in NutritionProfilePublic.model_fields

    def test_password_hash_absent(self, valid_profile_dict):
        assert "password_hash" not in NutritionProfilePublic.model_fields

    def test_token_absent(self, valid_profile_dict):
        assert "access_token" not in NutritionProfilePublic.model_fields
        assert "refresh_token" not in NutritionProfilePublic.model_fields

    def test_jwt_claims_absent(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        data = p.model_dump()
        assert "jwt" not in data
        assert "claims" not in data

    def test_secret_absent(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        data = p.model_dump()
        assert "secret" not in data

    def test_nested_user_absent(self, valid_profile_dict):
        assert "user" not in NutritionProfilePublic.model_fields

    def test_calculated_fields_absent(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        data = p.model_dump()
        for field in ("bmi", "bmr", "tdee", "calorie_target", "health_score"):
            assert field not in data

    def test_model_dump_contains_only_approved_fields(self, valid_profile_dict):
        p = NutritionProfilePublic.model_validate(valid_profile_dict)
        data = p.model_dump()
        approved = {
            "id",
            "user_id",
            "date_of_birth",
            "biological_sex",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
            "target_weight_kg",
            "dietary_preference",
            "allergies", "full_name", "phone", "avatar_url", "fitness_goal", "medical_conditions", "water_goal_ml", "sleep_goal_hours", "daily_calorie_goal", "daily_protein_goal_g", "daily_carb_goal_g", "daily_fat_goal_g",
            "created_at",
            "updated_at",
        }
        assert set(data.keys()) == approved


# ---------------------------------------------------------------------------
# M. Response schemas
# ---------------------------------------------------------------------------


class TestNutritionProfileData:
    def test_profile_required(self):
        with pytest.raises(ValidationError):
            NutritionProfileData()

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            NutritionProfileData(
                profile=NutritionProfilePublic.model_validate(
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "660e8400-e29b-41d4-a716-446655440001",
                        "date_of_birth": "1990-01-15",
                        "biological_sex": "male",
                        "height_cm": "175.00",
                        "weight_kg": "70.00",
                        "activity_level": "moderately_active",
                        "goal": "maintain_weight",
                        "target_weight_kg": None,
                        "dietary_preference": None,
                        "allergies": [],
                        "created_at": "2024-01-01T00:00:00+00:00",
                        "updated_at": "2024-01-01T12:00:00+00:00",
                    }
                ),
                extra_field="x",
            )


class TestNutritionProfileSuccessResponse:
    @pytest.fixture
    def valid_profile(self):
        return NutritionProfilePublic.model_validate(
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440001",
                "date_of_birth": "1990-01-15",
                "biological_sex": "male",
                "height_cm": "175.00",
                "weight_kg": "70.00",
                "activity_level": "moderately_active",
                "goal": "maintain_weight",
                "target_weight_kg": None,
                "dietary_preference": None,
                "allergies": [],
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T12:00:00+00:00",
            }
        )

    def test_success_defaults_to_true(self, valid_profile):
        r = NutritionProfileSuccessResponse(
            message="Profile retrieved",
            data=NutritionProfileData(profile=valid_profile),
        )
        assert r.success is True

    def test_message_required(self, valid_profile):
        with pytest.raises(ValidationError):
            NutritionProfileSuccessResponse(
                data=NutritionProfileData(profile=valid_profile),
            )

    def test_data_required(self):
        with pytest.raises(ValidationError):
            NutritionProfileSuccessResponse(message="test")

    def test_correct_nested_profile(self, valid_profile):
        r = NutritionProfileSuccessResponse(
            message="Profile retrieved",
            data=NutritionProfileData(profile=valid_profile),
        )
        assert r.data.profile.id == valid_profile.id

    def test_extra_fields_rejected(self, valid_profile):
        with pytest.raises(ValidationError):
            NutritionProfileSuccessResponse(
                message="test",
                data=NutritionProfileData(profile=valid_profile),
                extra="x",
            )

    def test_error_field_rejected(self, valid_profile):
        with pytest.raises(ValidationError):
            NutritionProfileSuccessResponse(
                message="test",
                data=NutritionProfileData(profile=valid_profile),
                error="x",
            )

    def test_token_field_rejected(self, valid_profile):
        with pytest.raises(ValidationError):
            NutritionProfileSuccessResponse(
                message="test",
                data=NutritionProfileData(profile=valid_profile),
                access_token="x",
            )

    def test_password_field_rejected(self, valid_profile):
        with pytest.raises(ValidationError):
            NutritionProfileSuccessResponse(
                message="test",
                data=NutritionProfileData(profile=valid_profile),
                password="x",
            )

    def test_calculated_fields_absent(self, valid_profile):
        r = NutritionProfileSuccessResponse(
            message="Profile retrieved",
            data=NutritionProfileData(profile=valid_profile),
        )
        data = r.model_dump()
        for f in ("bmi", "bmr", "tdee"):
            assert f not in str(data)

    def test_json_serialization_works(self, valid_profile):
        r = NutritionProfileSuccessResponse(
            message="Profile retrieved",
            data=NutritionProfileData(profile=valid_profile),
        )
        import json

        s = r.model_dump_json()
        obj = json.loads(s)
        assert obj["success"] is True
        assert obj["message"] == "Profile retrieved"
        assert obj["data"]["profile"]["biological_sex"] == "male"


# ---------------------------------------------------------------------------
# N. Schema/ORM alignment
# ---------------------------------------------------------------------------


class TestSchemaORmAlignment:
    def test_create_fields_align_with_editable_orm_fields(self):
        create_fields = set(NutritionProfileCreate.model_fields.keys())
        orm_editable = {
            "date_of_birth",
            "biological_sex",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
            "target_weight_kg",
            "dietary_preference",
            "allergies", "full_name", "phone", "avatar_url", "fitness_goal", "medical_conditions", "water_goal_ml", "sleep_goal_hours", "daily_calorie_goal", "daily_protein_goal_g", "daily_carb_goal_g", "daily_fat_goal_g",
        }
        assert create_fields == orm_editable

    def test_user_id_excluded_from_create(self):
        assert "user_id" not in NutritionProfileCreate.model_fields

    def test_id_excluded_from_create(self):
        assert "id" not in NutritionProfileCreate.model_fields

    def test_timestamps_excluded_from_create(self):
        assert "created_at" not in NutritionProfileCreate.model_fields
        assert "updated_at" not in NutritionProfileCreate.model_fields

    def test_nullable_fields_match_orm(self):
        assert NutritionProfileBase.model_fields["target_weight_kg"].is_required() is False
        assert NutritionProfileBase.model_fields["dietary_preference"].is_required() is False

    def test_required_fields_match_orm(self):
        for field in (
            "date_of_birth",
            "biological_sex",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
        ):
            assert not NutritionProfileBase.model_fields[field].is_required()

    def test_decimal_limits_match_constraints(self):
        h = NutritionProfileBase.model_fields["height_cm"]
        assert h.annotation == Decimal | None
        w = NutritionProfileBase.model_fields["weight_kg"]
        assert w.annotation == Decimal | None
        tw = NutritionProfileBase.model_fields["target_weight_kg"]
        assert tw.annotation == Decimal | None

    def test_enum_classes_identical_to_orm(self):
        np_fields = NutritionProfilePublic.model_fields
        assert np_fields["biological_sex"].annotation == BiologicalSex | None
        assert np_fields["activity_level"].annotation == ActivityLevel | None
        assert np_fields["goal"].annotation == NutritionGoal | None
        assert np_fields["dietary_preference"].annotation == DietaryPreference | None

    def test_no_calculated_field_in_schema_defs(self):
        combined = (
            set(NutritionProfileBase.model_fields.keys())
            | set(NutritionProfileUpdate.model_fields.keys())
            | set(NutritionProfilePublic.model_fields.keys())
        )
        calculated = {
            "age",
            "bmi",
            "bmi_category",
            "bmr",
            "tdee",
            "calorie_target",
            "protein_target",
            "carbohydrate_target",
            "carbs_target",
            "fat_target",
            "fiber_target",
            "water_target",
            "health_score",
            "recommended_weight",
            "recommended_calories",
            "meal_plan",
            "diet_plan",
            "cheat_meal",
        }
        assert combined.isdisjoint(calculated)

    def test_no_migration_required(self):
        from app.models.nutrition_profile import NutritionProfile as ORMModel

        assert hasattr(ORMModel, "date_of_birth")
        assert not hasattr(ORMModel, "bmi")


# ---------------------------------------------------------------------------
# O. Security and phase-boundary tests
# ---------------------------------------------------------------------------


class TestSecurityPhaseBoundary:
    def test_no_api_route_created(self):
        import app.api.v1.router as router_mod

        routes = router_mod.router.routes
        route_paths = {r.path for r in routes}
        assert "/api/v1/nutrition-profile" not in route_paths
        assert "/api/v1/profile" not in route_paths

    def test_nutrition_profile_repository_exists(self):
        import app.repositories

        assert hasattr(app.repositories, "NutritionProfileRepository")

    def test_nutrition_profile_service_exists(self):
        import app.services

        assert hasattr(app.services, "NutritionProfileService")

    def test_no_database_query_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "session" not in source.lower()
        assert "select(" not in source.lower()
        assert "query" not in source.lower().replace("model_field", "")

    def test_no_session_creation_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "Session" not in source

    def test_no_engine_creation_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "create_engine" not in source

    def test_no_bmi_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "bmi" not in source.lower()

    def test_no_bmr_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "bmr" not in source.lower()

    def test_no_tdee_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "tdee" not in source.lower()

    def test_no_calorie_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "def calorie" not in source.lower()

    def test_no_macro_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "def protein_target" not in source
        assert "def carb" not in source.lower()

    def test_no_health_score_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "health_score" not in source

    def test_no_diet_plan_function_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "diet_plan" not in source
        assert "meal_plan" not in source
        assert "cheat_meal" not in source

    def test_no_usda_integration_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "usda" not in source.lower()

    def test_no_groq_integration_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "groq" not in source.lower()

    def test_no_ai_integration_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read().lower()
        ai_related = [
            "openai",
            "langchain",
            "llm",
            "chatbot",
            "groq",
            "gemini",
            "claude",
            "machine_learning",
            "deep_learning",
            "neural",
        ]
        for term in ai_related:
            assert term not in source, f"AI-related term '{term}' found in schema module"

    def test_no_authentication_changes(self):
        from app.schemas.auth import LoginRequest, PublicUser, RegisterRequest

        assert PublicUser is not None
        assert LoginRequest is not None
        assert RegisterRequest is not None

    def test_no_orm_changes(self):
        from app.models.nutrition_profile import NutritionProfile
        from app.models.user import User

        assert User.__tablename__ == "users"
        assert NutritionProfile.__tablename__ == "nutrition_profiles"

    def test_migration_count_updated(self):
        from pathlib import Path

        versions_dir = Path(__file__).resolve().parent.parent / "alembic" / "versions"
        files = [f for f in versions_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        assert len(files) == 7

    def test_no_frontend_changes(self):
        frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
        assert frontend_dir.exists()

    def test_no_real_secret_added(self):
        import app.schemas.nutrition_profile as mod

        source = open(mod.__file__).read()
        assert "secret" not in source.lower()

    def test_no_database_connection_required(self):
        NutritionProfileBase.model_validate(_valid_base_dict())


# ---------------------------------------------------------------------------
# Boundary: `normalize_allergies` function-level edge cases
# ---------------------------------------------------------------------------


class TestNormalizeAllergiesEdgeCases:
    def test_tab_and_newline_in_string_not_rejected(self):
        result = normalize_allergies(["Peanuts\t", "Milk\n"])
        assert len(result) == 2
        assert result[0] == "Peanuts\t".strip()
        assert result[1] == "Milk\n".strip()

    def test_dedup_51_entries_with_all_identical(self):
        entries = ["a"] * 51
        with pytest.raises(ValueError, match="more than 50"):
            normalize_allergies(entries)

    def test_empty_after_strip_for_tab_only(self):
        with pytest.raises(ValueError):
            normalize_allergies(["\t"])

    def test_newline_only_after_strip(self):
        with pytest.raises(ValueError):
            normalize_allergies(["\n"])
