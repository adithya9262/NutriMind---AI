"""Tests for the NutritionLog migration content.

These tests inspect the migration file statically and verify Alembic
revision metadata. They do NOT connect to a database or apply migrations.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _migration_files() -> list[Path]:
    return sorted(
        f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
    )


def _nutrition_log_migration_text() -> str:
    files = _migration_files()
    new = [f for f in files if "b8a7c3d9e1f2" in f.name]
    assert len(new) == 1
    return new[0].read_text(encoding="utf-8")


def _nutrition_log_migration_module():
    import importlib.util

    files = _migration_files()
    new = [f for f in files if "b8a7c3d9e1f2" in f.name]
    assert len(new) == 1
    spec = importlib.util.spec_from_file_location("_nl_migration", new[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Migration graph
# ---------------------------------------------------------------------------


class TestNutritionLogMigrationGraph:
    def test_exactly_five_migration_revisions(self):
        assert len(_migration_files()) == 7

    def test_new_revision_down_revision_is_phase2(self):
        mod = _nutrition_log_migration_module()
        assert mod.down_revision == "99a3b19be1b8"

    def test_exactly_one_migration_head(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        heads = script.get_heads()
        assert len(heads) == 1

    def test_exactly_one_migration_base(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        bases = script.get_bases()
        assert len(bases) == 1

    def test_no_branches(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        for rev in script.walk_revisions():
            if rev.down_revision is None:
                continue
            assert rev.down_revision is not None

    def test_no_cycles(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        seen: set[str] = set()
        stack: list[str] = list(script.get_bases())
        while stack:
            rev = stack.pop()
            if rev in seen:
                raise AssertionError(f"Cycle detected at revision {rev}")
            seen.add(rev)
            rev_obj = script.get_revision(rev)
            if rev_obj and rev_obj.nextrev:
                stack.extend(rev_obj.nextrev)
        all_revs = list(script.walk_revisions())
        assert len(seen) == len(all_revs)

    def test_previous_revisions_unchanged(self):
        files = _migration_files()
        baseline = [f for f in files if "3f0c6eb4f49e" in f.name]
        phase2 = [f for f in files if "99a3b19be1b8" in f.name]
        assert len(baseline) == 1
        assert len(phase2) == 1


# ---------------------------------------------------------------------------
# Upgrade content
# ---------------------------------------------------------------------------


class TestNutritionLogUpgradeContent:
    def test_creates_nutrition_logs_table(self):
        text = _nutrition_log_migration_text()
        assert '"nutrition_logs"' in text or "'nutrition_logs'" in text

    def test_creates_exactly_one_new_table(self):
        text = _nutrition_log_migration_text()
        count = text.count("op.create_table(")
        assert count == 1, f"Expected 1 create_table call, found {count}"

    def test_creates_meal_type_enum(self):
        text = _nutrition_log_migration_text()
        assert 'name="meal_type"' in text

    def test_creates_lookup_index(self):
        text = _nutrition_log_migration_text()
        assert "op.create_index(" in text
        assert "ix_nutrition_logs_user_id_logged_date" in text

    def test_no_seed_data(self):
        text = _nutrition_log_migration_text()
        assert "op.execute(" not in text.split("def upgrade")[1].split("def downgrade")[0]
        assert "insert(" not in text

    def test_no_credentials(self):
        text = _nutrition_log_migration_text()
        assert "://" not in text
        assert "password" not in text.lower()

    def test_does_not_recreate_users(self):
        text = _nutrition_log_migration_text()
        assert '"users"' not in text.split("def upgrade")[1].split("def downgrade")[0]

    def test_does_not_recreate_nutrition_profiles(self):
        text = _nutrition_log_migration_text()
        assert '"nutrition_profiles"' not in text.split("def upgrade")[1].split("def downgrade")[0]


# ---------------------------------------------------------------------------
# Tables schema
# ---------------------------------------------------------------------------


class TestNutritionLogMigrationSchema:
    def test_id_column(self):
        text = _nutrition_log_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text

    def test_user_id_column(self):
        text = _nutrition_log_migration_text()
        assert 'sa.Column("user_id", sa.Uuid(), nullable=False)' in text

    def test_logged_date_column_type(self):
        text = _nutrition_log_migration_text()
        assert 'sa.Column("logged_date", sa.Date(), nullable=False)' in text

    def test_entry_id_column_type(self):
        text = _nutrition_log_migration_text()
        assert 'sa.Column("entry_id", sa.Uuid(), nullable=False)' in text

    def test_food_name_column(self):
        text = _nutrition_log_migration_text()
        assert 'sa.Column("food_name", sa.String(length=200), nullable=False)' in text

    def test_serving_description_column(self):
        text = _nutrition_log_migration_text()
        assert 'sa.Column("serving_description", sa.String(length=200), nullable=False)' in text

    def test_calories_kcal_numeric_precision(self):
        text = _nutrition_log_migration_text()
        assert "Numeric(precision=7, scale=2)" in text.split("calories_kcal")[1][:200]

    def test_protein_g_numeric_precision(self):
        text = _nutrition_log_migration_text()
        assert "Numeric(precision=6, scale=2)" in text.split("protein_g")[1][:200]

    def test_carbohydrate_g_numeric_precision(self):
        text = _nutrition_log_migration_text()
        assert "Numeric(precision=6, scale=2)" in text.split("carbohydrate_g")[1][:200]

    def test_fat_g_numeric_precision(self):
        text = _nutrition_log_migration_text()
        assert "Numeric(precision=6, scale=2)" in text.split("fat_g")[1][:200]

    def test_numeric_scale_is_two(self):
        text = _nutrition_log_migration_text()
        for col in ["calories_kcal", "protein_g", "carbohydrate_g", "fat_g"]:
            assert "scale=2)" in text.split(col)[1][:200]

    def test_created_at_timezone(self):
        text = _nutrition_log_migration_text()
        nl_section = text.split("nutrition_logs")[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in nl_section.split("created_at")[1][:200]

    def test_updated_at_timezone(self):
        text = _nutrition_log_migration_text()
        nl_section = text.split("nutrition_logs")[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in nl_section.split("updated_at")[1][:200]


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


class TestNutritionLogMigrationConstraints:
    def test_primary_key(self):
        text = _nutrition_log_migration_text()
        assert 'sa.PrimaryKeyConstraint("id")' in text

    def test_foreign_key_targets_users_id(self):
        text = _nutrition_log_migration_text()
        assert '"users.id"' in text or "'users.id'" in text

    def test_foreign_key_ondelete_cascade(self):
        text = _nutrition_log_migration_text()
        assert 'ondelete="CASCADE"' in text

    def test_foreign_key_name(self):
        text = _nutrition_log_migration_text()
        assert 'name="fk_nutrition_logs_user_id"' in text

    def test_composite_unique_constraint(self):
        text = _nutrition_log_migration_text()
        assert 'name="uq_nutrition_logs_user_id_entry_id"' in text

    def test_composite_unique_columns(self):
        text = _nutrition_log_migration_text()
        assert '"user_id"' in text
        assert '"entry_id"' in text
        assert 'name="uq_nutrition_logs_user_id_entry_id"' in text

    def test_calories_check_constraint(self):
        text = _nutrition_log_migration_text()
        assert 'name="ck_nutrition_logs_calories_kcal_range"' in text

    def test_protein_check_constraint(self):
        text = _nutrition_log_migration_text()
        assert 'name="ck_nutrition_logs_protein_g_range"' in text

    def test_carbohydrate_check_constraint(self):
        text = _nutrition_log_migration_text()
        assert 'name="ck_nutrition_logs_carbohydrate_g_range"' in text

    def test_fat_check_constraint(self):
        text = _nutrition_log_migration_text()
        assert 'name="ck_nutrition_logs_fat_g_range"' in text

    def test_check_constraint_expressions(self):
        text = _nutrition_log_migration_text()
        assert "calories_kcal >= 0 AND calories_kcal <= 10000" in text
        assert "protein_g >= 0 AND protein_g <= 1000" in text
        assert "carbohydrate_g >= 0 AND carbohydrate_g <= 2000" in text
        assert "fat_g >= 0 AND fat_g <= 1000" in text

    def test_lookup_index_exists(self):
        text = _nutrition_log_migration_text()
        assert "ix_nutrition_logs_user_id_logged_date" in text

    def test_lookup_index_columns(self):
        text = _nutrition_log_migration_text()
        assert '"user_id"' in text
        assert '"logged_date"' in text
        assert "ix_nutrition_logs_user_id_logged_date" in text

    def test_no_redundant_indexes(self):
        text = _nutrition_log_migration_text()
        lines = text.split("\n")
        index_count = sum(1 for line in lines if "op.create_index(" in line)
        assert index_count == 1, f"Expected 1 index, found {index_count}"


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------


class TestNutritionLogMigrationEnum:
    def test_meal_type_enum_created_once(self):
        text = _nutrition_log_migration_text()
        count = text.count('name="meal_type"')
        assert count == 1, f"Expected 1 meal_type reference, found {count}"

    def test_meal_type_values_are_lowercase(self):
        text = _nutrition_log_migration_text()
        assert '"breakfast"' in text
        assert '"lunch"' in text
        assert '"dinner"' in text
        assert '"snack"' in text

    def test_meal_type_has_exactly_four_values(self):
        text = _nutrition_log_migration_text()
        # Find the sa.Enum with name="meal_type" and count the values.
        import re

        pattern = r"sa\.Enum\(\s*\"([^\"]+)\".*?name=\"meal_type\""
        match = re.search(pattern, text, re.DOTALL)
        assert match is not None, "Could not find sa.Enum for meal_type"
        line = match.group(0)
        before_name = re.sub(r',\s*name="[^"]+"', "", line)
        values = re.findall(r'"([^"]+)"', before_name)
        assert len(values) == 4, f"Expected 4 enum values, found {len(values)}: {values}"

    def test_no_duplicate_enum_values(self):
        text = _nutrition_log_migration_text()
        import re

        pattern = r"sa\.Enum\(\s*\"([^\"]+)\".*?name=\"meal_type\""
        match = re.search(pattern, text, re.DOTALL)
        assert match is not None
        line = match.group(0)
        before_name = re.sub(r',\s*name="[^"]+"', "", line)
        values = re.findall(r'"([^"]+)"', before_name)
        assert len(values) == len(set(values)), f"Duplicate values found: {values}"


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


class TestNutritionLogDowngrade:
    def test_downgrade_drops_index(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.drop_index(" in downgrade

    def test_downgrade_drops_table(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.drop_table(" in downgrade

    def test_downgrade_drops_enum(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "DROP TYPE IF EXISTS" in downgrade
        assert "meal_type" in downgrade

    def test_downgrade_drops_enum_after_table(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        drop_table_pos = downgrade.index("op.drop_table(")
        drop_enum_pos = downgrade.index("DROP TYPE IF EXISTS")
        assert drop_table_pos < drop_enum_pos, "Table must be dropped before enum type"

    def test_downgrade_no_cascade(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "CASCADE" not in downgrade

    def test_downgrade_does_not_drop_users(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"users"' not in downgrade

    def test_downgrade_does_not_drop_nutrition_profiles(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"nutrition_profiles"' not in downgrade

    def test_downgrade_does_not_create_tables(self):
        text = _nutrition_log_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.create_table(" not in downgrade


# ---------------------------------------------------------------------------
# Forbidden content
# ---------------------------------------------------------------------------


class TestNutritionLogForbiddenContent:
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

    def test_no_computed_fields(self):
        text = _nutrition_log_migration_text()
        for field in self.FORBIDDEN_FIELDS:
            assert field not in text, f"Migration must not contain field '{field}'"

    def test_no_aggregation_fields(self):
        text = _nutrition_log_migration_text()
        no_agg = [
            "daily_totals",
            "meal_summaries",
            "remaining_calories",
            "remaining_protein",
            "remaining_carbohydrate",
            "remaining_fat",
            "over_target",
            "recommendation",
        ]
        for field in no_agg:
            assert field not in text, f"Migration must not contain field '{field}'"


# ---------------------------------------------------------------------------
# Boundary
# ---------------------------------------------------------------------------


class TestNutritionLogMigrationBoundary:
    def test_no_create_all_called(self):
        text = _nutrition_log_migration_text()
        assert "create_all" not in text

    def test_no_automatic_migration_execution(self):
        import app.main as app_main

        source = Path(app_main.__file__).read_text(encoding="utf-8")
        assert "alembic" not in source.lower()
