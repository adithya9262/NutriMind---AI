"""Tests for ORM model registration, structure, constraints, and relationships.

These tests inspect SQLAlchemy metadata only. They do not connect to a
database, create physical tables, or run migrations.
"""

from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.models import (
    ActivityLevel,
    BiologicalSex,
    BodyWeight,
    DietaryPreference,
    NutritionGoal,
    NutritionLog,
    NutritionProfile,
    User,
)

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


# ---------------------------------------------------------------------------
# Model registration
# ---------------------------------------------------------------------------


class TestModelRegistration:
    def test_users_table_in_metadata(self):
        assert "users" in Base.metadata.tables

    def test_nutrition_profiles_table_in_metadata(self):
        assert "nutrition_profiles" in Base.metadata.tables

    def test_only_application_tables_registered(self):
        registered = set(Base.metadata.tables.keys())
        expected = {"users", "nutrition_profiles", "nutrition_logs", "body_weights", "tasks", "goals"}
        assert registered == expected, f"Expected {expected}, got {registered}"

    def test_alembic_baseline_unchanged(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = [f for f in files if "3f0c6eb4f49e" in f.name]
        assert len(baseline) == 1
        assert "3f0c6eb4f49e" in baseline[0].name

    def test_new_migration_file_exists(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        assert len(files) >= 1


# ---------------------------------------------------------------------------
# User table structure
# ---------------------------------------------------------------------------


class TestUserTable:
    def test_table_name(self):
        assert User.__tablename__ == "users"

    def test_uuid_primary_key(self):
        col = User.__table__.c["id"]
        assert col.primary_key
        assert isinstance(col.type, sa.Uuid)

    def test_uuid_default_is_callable(self):
        default = User.__table__.c["id"].default
        assert default is not None
        val = default.arg(None)
        assert isinstance(val, UUID)

    def test_email_column(self):
        col = User.__table__.c["email"]
        assert not col.nullable
        assert isinstance(col.type, sa.String)
        assert col.type.length == 320

    def test_email_unique_constraint(self):
        constraints = [c for c in User.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        names = [c.name for c in constraints]
        assert "uq_users_email" in names

    def test_password_hash_column(self):
        col = User.__table__.c["password_hash"]
        assert not col.nullable
        assert isinstance(col.type, sa.String)
        assert col.type.length == 128

    def test_no_plaintext_password_column(self):
        assert "password" not in User.__table__.c

    def test_is_active_column(self):
        col = User.__table__.c["is_active"]
        assert not col.nullable
        assert isinstance(col.type, sa.Boolean)

    def test_is_active_default_true(self):
        col = User.__table__.c["is_active"]
        assert col.default is not None
        assert col.server_default is not None

    def test_is_verified_column(self):
        col = User.__table__.c["is_verified"]
        assert not col.nullable
        assert isinstance(col.type, sa.Boolean)

    def test_is_verified_default_false(self):
        col = User.__table__.c["is_verified"]
        assert col.default is not None
        assert col.server_default is not None

    def test_created_at_column(self):
        col = User.__table__.c["created_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_updated_at_column(self):
        col = User.__table__.c["updated_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_password_hash_not_in_repr(self):
        r = repr(User(id=UUID(int=0), email="test@example.com", password_hash="secret"))
        assert "password_hash" not in r
        assert "secret" not in r


# ---------------------------------------------------------------------------
# NutritionProfile table structure
# ---------------------------------------------------------------------------


class TestNutritionProfileTable:
    def test_table_name(self):
        assert NutritionProfile.__tablename__ == "nutrition_profiles"

    def test_uuid_primary_key(self):
        col = NutritionProfile.__table__.c["id"]
        assert col.primary_key
        assert isinstance(col.type, sa.Uuid)

    def test_user_id_foreign_key(self):
        col = NutritionProfile.__table__.c["user_id"]
        assert not col.nullable
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "users"
        assert fks[0].column.name == "id"

    def test_user_id_unique(self):
        constraints = [
            c for c in NutritionProfile.__table__.constraints if isinstance(c, sa.UniqueConstraint)
        ]
        user_id_unique = any(col.name == "user_id" for c in constraints for col in c.columns)
        assert user_id_unique

    def test_one_profile_per_user_constraint(self):
        constraints = [
            c for c in NutritionProfile.__table__.constraints if isinstance(c, sa.UniqueConstraint)
        ]
        names = [c.name for c in constraints]
        assert "uq_nutrition_profiles_user_id" in names

    def test_date_of_birth_type(self):
        col = NutritionProfile.__table__.c["date_of_birth"]
        assert isinstance(col.type, sa.Date)

    def test_height_cm_type(self):
        col = NutritionProfile.__table__.c["height_cm"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 5
        assert col.type.scale == 2

    def test_weight_kg_type(self):
        col = NutritionProfile.__table__.c["weight_kg"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 5
        assert col.type.scale == 2

    def test_target_weight_kg_type(self):
        col = NutritionProfile.__table__.c["target_weight_kg"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 5
        assert col.type.scale == 2

    def test_target_weight_kg_nullable(self):
        col = NutritionProfile.__table__.c["target_weight_kg"]
        assert col.nullable is True

    def test_core_fields_nullable(self):
        for col_name in [
            "date_of_birth",
            "biological_sex",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
        ]:
            col = NutritionProfile.__table__.c[col_name]
            assert col.nullable, f"{col_name} should be nullable"

    def test_user_id_non_null(self):
        col = NutritionProfile.__table__.c["user_id"]
        assert not col.nullable, "user_id should be non-null"

    def test_optional_fields_nullable(self):
        for col_name in [
            "target_weight_kg",
            "dietary_preference",
            "allergies",
        ]:
            col = NutritionProfile.__table__.c[col_name]
            assert col.nullable, f"{col_name} should be nullable"

    def test_height_check_constraint(self):
        checks = [
            c for c in NutritionProfile.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_profiles_height_cm_range" in names

    def test_weight_check_constraint(self):
        checks = [
            c for c in NutritionProfile.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_profiles_weight_kg_range" in names

    def test_target_weight_check_constraint(self):
        checks = [
            c for c in NutritionProfile.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_profiles_target_weight_kg_range" in names

    def test_allergies_uses_jsonb(self):
        col = NutritionProfile.__table__.c["allergies"]
        assert isinstance(col.type, JSONB)

    def test_allergies_default_is_callable(self):
        col = NutritionProfile.__table__.c["allergies"]
        assert col.default is not None
        assert callable(col.default.arg)

    def test_created_at_column(self):
        col = NutritionProfile.__table__.c["created_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_updated_at_column(self):
        col = NutritionProfile.__table__.c["updated_at"]
        assert not col.nullable
        assert col.type.timezone is True


# ---------------------------------------------------------------------------
# NutritionLog table structure
# ---------------------------------------------------------------------------


class TestNutritionLogTable:
    def test_table_name(self):
        assert NutritionLog.__tablename__ == "nutrition_logs"

    def test_is_base_subclass(self):
        assert issubclass(NutritionLog, Base)

    def test_uuid_primary_key(self):
        col = NutritionLog.__table__.c["id"]
        assert col.primary_key
        assert isinstance(col.type, sa.Uuid)

    def test_uuid_default_is_callable(self):
        default = NutritionLog.__table__.c["id"].default
        assert default is not None
        val = default.arg(None)
        assert isinstance(val, UUID)

    def test_user_id_column(self):
        col = NutritionLog.__table__.c["user_id"]
        assert not col.nullable
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "users"
        assert fks[0].column.name == "id"

    def test_user_id_foreign_key_name(self):
        col = NutritionLog.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.name == "fk_nutrition_logs_user_id"

    def test_user_id_ondelete_cascade(self):
        col = NutritionLog.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete == "CASCADE"

    def test_logged_date_column(self):
        col = NutritionLog.__table__.c["logged_date"]
        assert not col.nullable
        assert isinstance(col.type, sa.Date)

    def test_entry_id_column(self):
        col = NutritionLog.__table__.c["entry_id"]
        assert not col.nullable
        assert isinstance(col.type, sa.Uuid)

    def test_entry_id_not_globally_unique(self):
        uqs = [c for c in NutritionLog.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        for uq in uqs:
            if uq.name == "uq_nutrition_logs_user_id_entry_id":
                return
        raise AssertionError("Composite unique constraint not found")

    def test_composite_unique_columns(self):
        uqs = [c for c in NutritionLog.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        for uq in uqs:
            if uq.name == "uq_nutrition_logs_user_id_entry_id":
                cols = [col.name for col in uq.columns]
                assert cols == ["user_id", "entry_id"]
                return
        raise AssertionError("Composite unique constraint not found")

    def test_food_name_column(self):
        col = NutritionLog.__table__.c["food_name"]
        assert not col.nullable
        assert isinstance(col.type, sa.String)
        assert col.type.length == 200

    def test_meal_type_column(self):
        col = NutritionLog.__table__.c["meal_type"]
        assert not col.nullable
        assert col.type.name == "meal_type"

    def test_serving_description_column(self):
        col = NutritionLog.__table__.c["serving_description"]
        assert not col.nullable
        assert isinstance(col.type, sa.String)
        assert col.type.length == 200

    def test_calories_kcal_type(self):
        col = NutritionLog.__table__.c["calories_kcal"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 7
        assert col.type.scale == 2

    def test_protein_g_type(self):
        col = NutritionLog.__table__.c["protein_g"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 6
        assert col.type.scale == 2

    def test_carbohydrate_g_type(self):
        col = NutritionLog.__table__.c["carbohydrate_g"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 6
        assert col.type.scale == 2

    def test_fat_g_type(self):
        col = NutritionLog.__table__.c["fat_g"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 6
        assert col.type.scale == 2

    def test_no_float_types(self):
        for col_name in ["calories_kcal", "protein_g", "carbohydrate_g", "fat_g"]:
            col = NutritionLog.__table__.c[col_name]
            assert isinstance(col.type, sa.Numeric), f"{col_name} must be Numeric, not Float"

    def test_required_fields_non_null(self):
        for col_name in [
            "user_id",
            "logged_date",
            "entry_id",
            "food_name",
            "meal_type",
            "serving_description",
            "calories_kcal",
            "protein_g",
            "carbohydrate_g",
            "fat_g",
        ]:
            col = NutritionLog.__table__.c[col_name]
            assert not col.nullable, f"{col_name} should be non-null"

    def test_created_at_column(self):
        col = NutritionLog.__table__.c["created_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_updated_at_column(self):
        col = NutritionLog.__table__.c["updated_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_calories_check_constraint(self):
        checks = [
            c for c in NutritionLog.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_logs_calories_kcal_range" in names

    def test_protein_check_constraint(self):
        checks = [
            c for c in NutritionLog.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_logs_protein_g_range" in names

    def test_carbohydrate_check_constraint(self):
        checks = [
            c for c in NutritionLog.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_logs_carbohydrate_g_range" in names

    def test_fat_check_constraint(self):
        checks = [
            c for c in NutritionLog.__table__.constraints if isinstance(c, sa.CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_nutrition_logs_fat_g_range" in names

    def test_exactly_four_named_check_constraints(self):
        checks = [
            c
            for c in NutritionLog.__table__.constraints
            if isinstance(c, sa.CheckConstraint) and c.name
        ]
        assert len(checks) == 4

    def test_lookup_index_exists(self):
        indexes = [idx for idx in NutritionLog.__table__.indexes]
        names = [idx.name for idx in indexes]
        assert "ix_nutrition_logs_user_id_logged_date" in names

    def test_lookup_index_columns(self):
        for idx in NutritionLog.__table__.indexes:
            if idx.name == "ix_nutrition_logs_user_id_logged_date":
                cols = [col.name for col in idx.columns]
                assert cols == ["user_id", "logged_date"]
                assert not idx.unique
                return
        raise AssertionError("Lookup index not found")

    def test_no_redundant_indexes(self):
        expected_names = {"ix_nutrition_logs_user_id_logged_date"}
        actual_names = {idx.name for idx in NutritionLog.__table__.indexes}
        assert actual_names == expected_names, (
            f"Expected indexes {expected_names}, got {actual_names}"
        )

    def test_entry_id_not_global_unique_column(self):
        col = NutritionLog.__table__.c["entry_id"]
        assert not col.unique, "entry_id must not be globally unique"

    def test_meal_type_reuses_phase4f1_mealtype(self):
        col = NutritionLog.__table__.c["meal_type"]
        from app.core.nutrition_logs import MealType as DomainMealType

        assert col.type.enum_class is DomainMealType

    def test_meal_type_postgres_enum_name(self):
        col = NutritionLog.__table__.c["meal_type"]
        assert col.type.name == "meal_type"

    def test_meal_type_values_callable_persists_lowercase(self):
        col = NutritionLog.__table__.c["meal_type"]
        assert col.type.values_callable is not None
        enum_class = col.type.enum_class
        result = col.type.values_callable(enum_class)
        for member in enum_class:
            assert member.value in result
            assert member.name not in result


# ---------------------------------------------------------------------------
# BodyWeight table structure
# ---------------------------------------------------------------------------


class TestBodyWeightTable:
    def test_table_name(self):
        assert BodyWeight.__tablename__ == "body_weights"

    def test_is_base_subclass(self):
        assert issubclass(BodyWeight, Base)

    def test_uses_timestamp_mixin(self):
        assert hasattr(BodyWeight, "created_at")
        assert hasattr(BodyWeight, "updated_at")

    def test_uuid_primary_key(self):
        col = BodyWeight.__table__.c["id"]
        assert col.primary_key
        assert isinstance(col.type, sa.Uuid)

    def test_uuid_default_is_callable(self):
        default = BodyWeight.__table__.c["id"].default
        assert default is not None
        val = default.arg(None)
        assert isinstance(val, UUID)

    def test_exact_columns(self):
        columns = set(BodyWeight.__table__.c.keys())
        expected = {
            "id",
            "user_id",
            "entry_id",
            "logged_date",
            "weight_kg",
            "created_at",
            "updated_at",
        }
        assert columns == expected, f"Expected {expected}, got {columns}"

    def test_user_id_column(self):
        col = BodyWeight.__table__.c["user_id"]
        assert not col.nullable
        assert isinstance(col.type, sa.Uuid)

    def test_user_id_foreign_key(self):
        col = BodyWeight.__table__.c["user_id"]
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "users"
        assert fks[0].column.name == "id"

    def test_user_id_foreign_key_name(self):
        col = BodyWeight.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.name == "fk_body_weights_user_id"

    def test_user_id_ondelete_cascade(self):
        col = BodyWeight.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete == "CASCADE"

    def test_entry_id_column(self):
        col = BodyWeight.__table__.c["entry_id"]
        assert not col.nullable
        assert isinstance(col.type, sa.Uuid)

    def test_entry_id_no_default(self):
        col = BodyWeight.__table__.c["entry_id"]
        assert col.default is None, "entry_id must not have an ORM default"

    def test_entry_id_not_globally_unique(self):
        uqs = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        for uq in uqs:
            if uq.name == "uq_body_weights_user_id_entry_id":
                cols = [col.name for col in uq.columns]
                assert cols == ["user_id", "entry_id"]
                return
        raise AssertionError("Composite unique user_id+entry_id constraint not found")

    def test_logged_date_column(self):
        col = BodyWeight.__table__.c["logged_date"]
        assert not col.nullable
        assert isinstance(col.type, sa.Date)

    def test_logged_date_no_default(self):
        col = BodyWeight.__table__.c["logged_date"]
        assert col.default is None, "logged_date must not have an ORM default"

    def test_weight_kg_type(self):
        col = BodyWeight.__table__.c["weight_kg"]
        assert isinstance(col.type, sa.Numeric)
        assert col.type.precision == 5
        assert col.type.scale == 2

    def test_weight_kg_not_float(self):
        col = BodyWeight.__table__.c["weight_kg"]
        assert isinstance(col.type, sa.Numeric), "weight_kg must be Numeric, not Float"

    def test_weight_kg_numeric_scale_2(self):
        col = BodyWeight.__table__.c["weight_kg"]
        assert col.type.scale == 2

    def test_weight_kg_nullable(self):
        col = BodyWeight.__table__.c["weight_kg"]
        assert not col.nullable

    def test_created_at_column(self):
        col = BodyWeight.__table__.c["created_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_updated_at_column(self):
        col = BodyWeight.__table__.c["updated_at"]
        assert not col.nullable
        assert col.type.timezone is True

    def test_required_fields_non_null(self):
        for col_name in ["user_id", "entry_id", "logged_date", "weight_kg"]:
            col = BodyWeight.__table__.c[col_name]
            assert not col.nullable, f"{col_name} should be non-null"

    def test_date_unique_constraint(self):
        uqs = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        names = [c.name for c in uqs]
        assert "uq_body_weights_user_id_logged_date" in names

    def test_date_unique_constraint_columns(self):
        uqs = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        for uq in uqs:
            if uq.name == "uq_body_weights_user_id_logged_date":
                cols = [col.name for col in uq.columns]
                assert cols == ["user_id", "logged_date"]
                return
        raise AssertionError("Date uniqueness constraint not found")

    def test_entry_id_unique_constraint(self):
        uqs = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        names = [c.name for c in uqs]
        assert "uq_body_weights_user_id_entry_id" in names

    def test_weight_range_check_constraint(self):
        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        names = [c.name for c in checks]
        assert "ck_body_weights_weight_kg_range" in names

    def test_weight_lower_bound(self):
        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        for ck in checks:
            if ck.name == "ck_body_weights_weight_kg_range":
                sql_text = str(ck.sqltext)
                assert "10.00" in sql_text, f"Lower bound 10.00 missing from {sql_text}"
                return
        raise AssertionError("Weight range check constraint not found")

    def test_weight_upper_bound(self):
        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        for ck in checks:
            if ck.name == "ck_body_weights_weight_kg_range":
                sql_text = str(ck.sqltext)
                assert "700.00" in sql_text, f"Upper bound 700.00 missing from {sql_text}"
                return
        raise AssertionError("Weight range check constraint not found")

    def test_domain_alignment_lower_bound(self):
        from app.core.body_weight import MIN_BODY_WEIGHT_KG

        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        for ck in checks:
            if ck.name == "ck_body_weights_weight_kg_range":
                assert str(MIN_BODY_WEIGHT_KG) in str(ck.sqltext)
                return
        raise AssertionError("Weight range check constraint not found")

    def test_domain_alignment_upper_bound(self):
        from app.core.body_weight import MAX_BODY_WEIGHT_KG

        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        for ck in checks:
            if ck.name == "ck_body_weights_weight_kg_range":
                assert str(MAX_BODY_WEIGHT_KG) in str(ck.sqltext)
                return
        raise AssertionError("Weight range check constraint not found")

    def test_domain_alignment_scale(self):
        col = BodyWeight.__table__.c["weight_kg"]
        assert col.type.scale == 2
        assert col.type.precision == 5

    def test_exactly_two_unique_constraints(self):
        uqs = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        assert len(uqs) == 2, f"Expected 2 unique constraints, found {len(uqs)}"

    def test_exactly_one_check_constraint(self):
        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        assert len(checks) == 1, f"Expected 1 check constraint, found {len(checks)}"

    def test_no_redundant_explicit_index(self):
        # The unique constraint on (user_id, logged_date) provides
        # equivalent B-tree indexing, so no explicit index is needed.
        indexes = [idx for idx in BodyWeight.__table__.indexes]
        assert len(indexes) == 0, f"Expected 0 explicit indexes, found {len(indexes)}"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestBiologicalSexEnum:
    def test_values(self):
        assert BiologicalSex.MALE.value == "male"
        assert BiologicalSex.FEMALE.value == "female"
        assert BiologicalSex.OTHER.value == "other"
        assert BiologicalSex.PREFER_NOT_TO_SAY.value == "prefer_not_to_say"

    def test_member_count(self):
        assert len(BiologicalSex) == 4

    def test_no_duplicate_values(self):
        values = [e.value for e in BiologicalSex]
        assert len(values) == len(set(values))


class TestActivityLevelEnum:
    def test_values(self):
        assert ActivityLevel.SEDENTARY.value == "sedentary"
        assert ActivityLevel.LIGHTLY_ACTIVE.value == "lightly_active"
        assert ActivityLevel.MODERATELY_ACTIVE.value == "moderately_active"
        assert ActivityLevel.VERY_ACTIVE.value == "very_active"
        assert ActivityLevel.EXTRA_ACTIVE.value == "extra_active"

    def test_member_count(self):
        assert len(ActivityLevel) == 5

    def test_no_duplicate_values(self):
        values = [e.value for e in ActivityLevel]
        assert len(values) == len(set(values))


class TestNutritionGoalEnum:
    def test_values(self):
        assert NutritionGoal.LOSE_WEIGHT.value == "lose_weight"
        assert NutritionGoal.MAINTAIN_WEIGHT.value == "maintain_weight"
        assert NutritionGoal.GAIN_WEIGHT.value == "gain_weight"
        assert NutritionGoal.GAIN_MUSCLE.value == "gain_muscle"

    def test_member_count(self):
        assert len(NutritionGoal) == 4

    def test_no_duplicate_values(self):
        values = [e.value for e in NutritionGoal]
        assert len(values) == len(set(values))


class TestDietaryPreferenceEnum:
    def test_values(self):
        assert DietaryPreference.NO_PREFERENCE.value == "no_preference"
        assert DietaryPreference.VEGETARIAN.value == "vegetarian"
        assert DietaryPreference.VEGAN.value == "vegan"
        assert DietaryPreference.PESCATARIAN.value == "pescatarian"
        assert DietaryPreference.EGGETARIAN.value == "eggetarian"

    def test_member_count(self):
        assert len(DietaryPreference) == 5

    def test_no_duplicate_values(self):
        values = [e.value for e in DietaryPreference]
        assert len(values) == len(set(values))


class TestEnumSqlAlchemyNames:
    def test_biological_sex_enum_name(self):
        col = NutritionProfile.__table__.c["biological_sex"]
        assert col.type.name == "biological_sex"

    def test_activity_level_enum_name(self):
        col = NutritionProfile.__table__.c["activity_level"]
        assert col.type.name == "activity_level"

    def test_nutrition_goal_enum_name(self):
        col = NutritionProfile.__table__.c["goal"]
        assert col.type.name == "nutrition_goal"

    def test_dietary_preference_enum_name(self):
        col = NutritionProfile.__table__.c["dietary_preference"]
        assert col.type.name == "dietary_preference"


class TestEnumValuesCallable:
    """Verify all four SQLAlchemy Enum columns use values_callable that
    persists Python StrEnum .value (lowercase) rather than .name (uppercase)."""

    def _assert_uses_values_callable(self, col):
        assert col.type.values_callable is not None, f"{col.key} Enum is missing values_callable"
        # Invoke the callable with the enum class to verify it returns .value.
        enum_class = col.type.enum_class
        result = col.type.values_callable(enum_class)
        for member in enum_class:
            assert member.value in result, (
                f"{col.key}: {member.value} not in values_callable result"
            )
            assert member.name not in result, (
                f"{col.key}: values_callable must not return .name ({member.name})"
            )

    def test_biological_sex_values_callable(self):
        self._assert_uses_values_callable(NutritionProfile.__table__.c["biological_sex"])

    def test_activity_level_values_callable(self):
        self._assert_uses_values_callable(NutritionProfile.__table__.c["activity_level"])

    def test_nutrition_goal_values_callable(self):
        self._assert_uses_values_callable(NutritionProfile.__table__.c["goal"])

    def test_dietary_preference_values_callable(self):
        self._assert_uses_values_callable(NutritionProfile.__table__.c["dietary_preference"])


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


class TestRelationships:
    def test_user_to_nutrition_profile_one_to_one(self):
        rel = User.__mapper__.relationships["nutrition_profile"]
        assert rel.uselist is False
        assert rel.back_populates == "user"

    def test_nutrition_profile_to_user_back_populates(self):
        rel = NutritionProfile.__mapper__.relationships["user"]
        assert rel.back_populates == "nutrition_profile"

    def test_cascade_is_all_delete_orphan(self):
        rel = User.__mapper__.relationships["nutrition_profile"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True
        assert rel.cascade.save_update is True
        assert rel.cascade.merge is True
        assert rel.cascade.refresh_expire is True
        assert rel.cascade.expunge is True
        assert rel.single_parent is True

    def test_foreign_key_ondelete_is_cascade(self):
        col = NutritionProfile.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete == "CASCADE"

    def test_bidirectional_relationship(self):
        user_rel = User.__mapper__.relationships["nutrition_profile"]
        profile_rel = NutritionProfile.__mapper__.relationships["user"]
        assert user_rel.mapper.class_ is NutritionProfile
        assert profile_rel.mapper.class_ is User

    def test_user_to_nutrition_logs_one_to_many(self):
        rel = User.__mapper__.relationships["nutrition_logs"]
        assert rel.uselist is True
        assert rel.back_populates == "user"

    def test_nutrition_log_to_user_back_populates(self):
        rel = NutritionLog.__mapper__.relationships["user"]
        assert rel.back_populates == "nutrition_logs"

    def test_nutrition_log_user_cascade(self):
        rel = User.__mapper__.relationships["nutrition_logs"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True

    def test_existing_profile_relationship_unchanged(self):
        profile_rel = User.__mapper__.relationships["nutrition_profile"]
        assert profile_rel.uselist is False
        assert profile_rel.back_populates == "user"
        assert profile_rel.single_parent is True

    def test_user_to_body_weights_one_to_many(self):
        rel = User.__mapper__.relationships["body_weights"]
        assert rel.uselist is True
        assert rel.back_populates == "user"

    def test_body_weight_to_user_back_populates(self):
        rel = BodyWeight.__mapper__.relationships["user"]
        assert rel.back_populates == "body_weights"

    def test_body_weight_user_cascade(self):
        rel = User.__mapper__.relationships["body_weights"]
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True

    def test_body_weight_relationship_bidirectional(self):
        user_rel = User.__mapper__.relationships["body_weights"]
        bw_rel = BodyWeight.__mapper__.relationships["user"]
        assert user_rel.mapper.class_ is BodyWeight
        assert bw_rel.mapper.class_ is User


# ---------------------------------------------------------------------------
# Forbidden fields
# ---------------------------------------------------------------------------


class TestForbiddenFields:
    FORBIDDEN_FIELDS = [
        "age",
        "bmi",
        "bmr",
        "tdee",
        "calorie_target",
        "protein_target",
        "carbohydrate_target",
        "fat_target",
        "health_score",
    ]

    def test_user_has_no_forbidden_fields(self):
        columns = set(User.__table__.c.keys())
        for field in self.FORBIDDEN_FIELDS:
            assert field not in columns, f"User should not have field '{field}'"

    def test_nutrition_profile_has_no_forbidden_fields(self):
        columns = set(NutritionProfile.__table__.c.keys())
        for field in self.FORBIDDEN_FIELDS:
            assert field not in columns, f"NutritionProfile should not have field '{field}'"

    def test_nutrition_log_has_no_forbidden_fields(self):
        columns = set(NutritionLog.__table__.c.keys())
        for field in self.FORBIDDEN_FIELDS:
            assert field not in columns, f"NutritionLog should not have field '{field}'"

    def test_nutrition_log_no_aggregation_fields(self):
        columns = set(NutritionLog.__table__.c.keys())
        no_aggregation = {
            "daily_totals",
            "meal_summaries",
            "remaining_calories",
            "remaining_protein",
            "remaining_carbohydrate",
            "remaining_fat",
            "over_target",
            "health_score",
            "recommendation",
        }
        for field in no_aggregation:
            assert field not in columns, f"NutritionLog should not have field '{field}'"

    def test_no_jwt_fields_in_user(self):
        columns = set(User.__table__.c.keys())
        for field in {"jwt", "refresh_token", "token"}:
            assert field not in columns, f"User should not have field '{field}'"

    def test_no_plaintext_password(self):
        assert "password" not in User.__table__.c, "User should not have a column named 'password'"


# ---------------------------------------------------------------------------
# Migration boundary
# ---------------------------------------------------------------------------


class TestMigrationBoundary:
    def test_at_least_one_migration_revision(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        assert len(files) >= 1

    def test_baseline_revision_id(self):
        files = [f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
        baseline = [f for f in files if "3f0c6eb4f49e" in f.name]
        assert len(baseline) >= 1
