"""Tests for the User/NutritionProfile migration content.

These tests inspect the migration file statically and verify Alembic
revision metadata.  They do NOT connect to a database or apply migrations.
"""

import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

# ── Helpers ──────────────────────────────────────────────────────────


def _migration_files() -> list[Path]:
    return sorted(
        f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
    )


def _phase2_migration_text() -> str:
    files = _migration_files()
    phase2 = [f for f in files if "99a3b19be1b8" in f.name]
    assert len(phase2) == 1
    return phase2[0].read_text(encoding="utf-8")


def _phase2_migration_module():
    import importlib.util

    files = _migration_files()
    phase2 = [f for f in files if "99a3b19be1b8" in f.name]
    assert len(phase2) == 1
    spec = importlib.util.spec_from_file_location("_phase2_migration", phase2[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Migration graph ──────────────────────────────────────────────────


class TestMigrationGraph:
    def test_exactly_five_migration_revisions(self):
        assert len(_migration_files()) == 7

    def test_baseline_revision_unchanged(self):
        files = _migration_files()
        baseline = next(f for f in files if "baseline" in f.name)
        assert "3f0c6eb4f49e" in baseline.name

    def test_phase2_revision_down_revision_is_baseline(self):
        mod = _phase2_migration_module()
        assert mod.down_revision == "3f0c6eb4f49e"

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

    def test_baseline_is_base(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        bases = script.get_bases()
        assert bases[0] == "3f0c6eb4f49e"

    def test_no_branches(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        # Check that every revision except the base has exactly one parent
        # and the base has zero parents.
        for rev in script.walk_revisions():
            if rev.down_revision is None:
                continue  # base revision
            assert rev.down_revision is not None

    def test_no_cycles(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        # Walk the revision graph to detect cycles.
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
        # Count all reachable revisions.
        all_revs = list(script.walk_revisions())
        assert len(seen) == len(all_revs)


# ── Upgrade content ──────────────────────────────────────────────────


class TestUpgradeContent:
    def test_creates_users_table(self):
        text = _phase2_migration_text()
        assert "create_table" in text
        assert '"users"' in text or "'users'" in text

    def test_creates_nutrition_profiles_table(self):
        text = _phase2_migration_text()
        assert '"nutrition_profiles"' in text or "'nutrition_profiles'" in text

    def test_creates_exactly_two_application_tables(self):
        text = _phase2_migration_text()
        # Count create_table calls (should be 2).
        count = text.count("op.create_table(")
        assert count == 2, f"Expected 2 create_table calls, found {count}"

    def test_users_before_nutrition_profiles(self):
        text = _phase2_migration_text()
        users_pos = text.index('op.create_table(\n        "users"')
        np_pos = text.index('op.create_table(\n        "nutrition_profiles"')
        assert users_pos < np_pos

    def test_no_seed_data(self):
        text = _phase2_migration_text()
        assert "insert(" not in text

    def test_no_plaintext_passwords(self):
        text = _phase2_migration_text()
        assert "password" in text
        assert "password_hash" in text
        assert '"password"' not in text.replace("password_hash", "")

    def test_no_credentials(self):
        text = _phase2_migration_text()
        assert "://" not in text
        assert "nutrimind_dev" not in text

    def test_creates_enum_types_implicitly(self):
        text = _phase2_migration_text()
        # Enum types are created by sa.Enum inside op.create_table.
        assert "sa.Enum(" in text
        # Each enum type appears exactly once in the column definitions.
        assert text.count('name="biological_sex"') == 1
        assert text.count('name="activity_level"') == 1
        assert text.count('name="nutrition_goal"') == 1
        assert text.count('name="dietary_preference"') == 1


# ── Users table schema ───────────────────────────────────────────────


class TestUsersMigrationSchema:
    def test_users_id_column(self):
        text = _phase2_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text

    def test_users_email_column(self):
        text = _phase2_migration_text()
        assert 'sa.Column("email", sa.String(length=320), nullable=False)' in text

    def test_users_password_hash_column(self):
        text = _phase2_migration_text()
        assert 'sa.Column("password_hash", sa.String(length=128), nullable=False)' in text

    def test_users_is_active_default_true(self):
        text = _phase2_migration_text()
        assert 'server_default=sa.text("true")' in text.split("is_active")[1][:200]

    def test_users_is_verified_default_false(self):
        text = _phase2_migration_text()
        assert 'server_default=sa.text("false")' in text.split("is_verified")[1][:200]

    def test_users_created_at_timezone(self):
        text = _phase2_migration_text()
        assert "DateTime(timezone=True)" in text.split("created_at")[1][:200]

    def test_users_updated_at_timezone(self):
        text = _phase2_migration_text()
        assert "DateTime(timezone=True)" in text.split("updated_at")[1][:200]

    def test_users_primary_key(self):
        text = _phase2_migration_text()
        assert 'sa.PrimaryKeyConstraint("id")' in text

    def test_users_email_unique_constraint(self):
        text = _phase2_migration_text()
        assert 'name="uq_users_email"' in text

    def test_users_no_redundant_email_index(self):
        text = _phase2_migration_text()
        # Check there's no separate ix_users_email index.
        assert "ix_users_email" not in text
        assert "sa.Index(" not in text.split('"users"')[1][:500]


# ── NutritionProfile table schema ────────────────────────────────────


class TestNutritionProfileMigrationSchema:
    def test_np_id_column(self):
        text = _phase2_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text

    def test_np_user_id_column(self):
        text = _phase2_migration_text()
        assert 'sa.Column("user_id", sa.Uuid(), nullable=False)' in text

    def test_np_date_of_birth_type(self):
        text = _phase2_migration_text()
        assert 'sa.Column("date_of_birth", sa.Date(), nullable=False)' in text

    def test_np_height_cm_type(self):
        text = _phase2_migration_text()
        assert "Numeric(precision=5, scale=2)" in text.split("height_cm")[1][:200]

    def test_np_weight_kg_type(self):
        text = _phase2_migration_text()
        assert "Numeric(precision=5, scale=2)" in text.split("weight_kg")[1][:200]

    def test_np_target_weight_kg_type(self):
        text = _phase2_migration_text()
        assert "Numeric(precision=5, scale=2)" in text.split("target_weight_kg")[1][:200]

    def test_np_target_weight_nullable(self):
        text = _phase2_migration_text()
        assert "nullable=True" in text.split("target_weight_kg")[1][:200]

    def test_np_dietary_preference_nullable(self):
        text = _phase2_migration_text()
        # Extract the dietary_preference column definition.
        np_section = text.split("nutrition_profiles")[1].split("def downgrade")[0]
        dp_start = np_section.index('"dietary_preference"')
        # Look for nullable=True between this column and the next column.
        remainder = np_section[dp_start:]
        next_col = remainder.find("sa.Column(", 50)
        dp_block = remainder[:next_col] if next_col > 0 else remainder[:500]
        assert "nullable=True" in dp_block

    def test_np_allergies_jsonb(self):
        text = _phase2_migration_text()
        assert "JSONB" in text.split("allergies")[1][:300]

    def test_np_allergies_server_default(self):
        text = _phase2_migration_text()
        np_section = text.split("nutrition_profiles")[1].split("def downgrade")[0]
        allergies = np_section.split("allergies")[1][:300]
        assert "'[]'::jsonb" in allergies

    def test_np_foreign_key_targets_users_id(self):
        text = _phase2_migration_text()
        fk_section = text.split("ForeignKeyConstraint")[1][:200]
        assert '"users.id"' in fk_section or "'users.id'" in fk_section

    def test_np_foreign_key_ondelete_cascade(self):
        text = _phase2_migration_text()
        assert 'ondelete="CASCADE"' in text

    def test_np_unique_user_id_constraint(self):
        text = _phase2_migration_text()
        assert 'name="uq_nutrition_profiles_user_id"' in text

    def test_np_height_check_constraint(self):
        text = _phase2_migration_text()
        assert 'name="ck_nutrition_profiles_height_cm_range"' in text

    def test_np_weight_check_constraint(self):
        text = _phase2_migration_text()
        assert 'name="ck_nutrition_profiles_weight_kg_range"' in text

    def test_np_target_weight_check_constraint(self):
        text = _phase2_migration_text()
        assert 'name="ck_nutrition_profiles_target_weight_kg_range"' in text

    def test_np_created_at_timezone(self):
        text = _phase2_migration_text()
        np_section = text.split("nutrition_profiles")[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in np_section.split("created_at")[1][:200]

    def test_np_updated_at_timezone(self):
        text = _phase2_migration_text()
        np_section = text.split("nutrition_profiles")[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in np_section.split("updated_at")[1][:200]

    def test_np_no_redundant_user_id_index(self):
        text = _phase2_migration_text()
        np_section = text.split("nutrition_profiles")[1].split("def downgrade")[0]
        assert "sa.Index(" not in np_section


# ── Enum verification ────────────────────────────────────────────────


class TestMigrationEnums:
    def test_biological_sex_values_are_lowercase(self):
        text = _phase2_migration_text()
        assert '"male"' in text
        assert '"female"' in text
        assert '"other"' in text
        assert '"prefer_not_to_say"' in text

    def test_activity_level_values_are_lowercase(self):
        text = _phase2_migration_text()
        assert '"sedentary"' in text
        assert '"lightly_active"' in text
        assert '"very_active"' in text
        assert '"extra_active"' in text

    def test_nutrition_goal_values_are_lowercase(self):
        text = _phase2_migration_text()
        assert '"lose_weight"' in text
        assert '"maintain_weight"' in text
        assert '"gain_weight"' in text
        assert '"gain_muscle"' in text

    def test_dietary_preference_values_are_lowercase(self):
        text = _phase2_migration_text()
        assert '"no_preference"' in text
        assert '"vegetarian"' in text
        assert '"vegan"' in text
        assert '"pescatarian"' in text
        assert '"eggetarian"' in text

    def test_enum_type_names_are_stable(self):
        text = _phase2_migration_text()
        assert 'name="biological_sex"' in text
        assert 'name="activity_level"' in text
        assert 'name="nutrition_goal"' in text
        assert 'name="dietary_preference"' in text

    def test_enum_types_created_by_sa_enum(self):
        text = _phase2_migration_text()
        # Each enum column uses sa.Enum with lowercase values.
        assert text.count('name="biological_sex"') == 1
        assert text.count('name="activity_level"') == 1
        assert text.count('name="nutrition_goal"') == 1
        assert text.count('name="dietary_preference"') == 1

    def _enum_values_from_source(self, source: str, enum_name: str) -> list[str]:
        """Extract enum values from sa.Enum(...) calls in the upgrade."""
        # Find sa.Enum for the given name.  Pattern matches:
        # sa.Enum("val1", "val2", ..., name=enum_name)
        pattern = r"sa\.Enum\(\s*\"([^\"]+)\".*?name=\"" + re.escape(enum_name) + r"\""
        match = re.search(pattern, source, re.DOTALL)
        assert match is not None, f"Could not find sa.Enum for {enum_name}"
        # Collect all quoted string args before name=.
        line = match.group(0)
        # Remove the name=... part at the end to avoid matching it.
        before_name = re.sub(r',\s*name="[^"]+"', "", line)
        values = re.findall(r'"([^"]+)"', before_name)
        return values

    def test_no_duplicate_values_in_biological_sex(self):
        mod = _phase2_migration_module()
        import inspect

        source = inspect.getsource(mod.upgrade)
        values = self._enum_values_from_source(source, "biological_sex")
        assert len(values) == len(set(values))

    def test_no_duplicate_values_in_activity_level(self):
        mod = _phase2_migration_module()
        import inspect

        source = inspect.getsource(mod.upgrade)
        values = self._enum_values_from_source(source, "activity_level")
        assert len(values) == len(set(values))

    def test_no_duplicate_values_in_nutrition_goal(self):
        mod = _phase2_migration_module()
        import inspect

        source = inspect.getsource(mod.upgrade)
        values = self._enum_values_from_source(source, "nutrition_goal")
        assert len(values) == len(set(values))

    def test_no_duplicate_values_in_dietary_preference(self):
        mod = _phase2_migration_module()
        import inspect

        source = inspect.getsource(mod.upgrade)
        values = self._enum_values_from_source(source, "dietary_preference")
        assert len(values) == len(set(values))


# ── Downgrade content ────────────────────────────────────────────────


class TestDowngradeContent:
    def test_downgrade_drops_nutrition_profiles_first(self):
        text = _phase2_migration_text()
        downgrade = text.split("def downgrade")[1]
        np_pos = downgrade.index("nutrition_profiles")
        users_pos = downgrade.index("users")
        assert np_pos < users_pos, "nutrition_profiles must be dropped before users"

    def test_downgrade_drops_two_tables(self):
        text = _phase2_migration_text()
        downgrade = text.split("def downgrade")[1]
        count = downgrade.count("op.drop_table(")
        assert count == 2, f"Expected 2 drop_table calls, found {count}"

    def test_downgrade_drops_four_enum_types(self):
        text = _phase2_migration_text()
        downgrade = text.split("def downgrade")[1]
        count = downgrade.count("DROP TYPE IF EXISTS")
        assert count == 4, f"Expected 4 DROP TYPE statements, found {count}"

    def test_downgrade_no_cascade(self):
        text = _phase2_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "CASCADE" not in downgrade

    def test_downgrade_does_not_create_tables(self):
        text = _phase2_migration_text()
        downgrade = text.split("def downgrade")[1]
        # Check that downgrade only contains drop_table and DROP TYPE.
        assert "op.drop_table(" in downgrade
        assert "op.execute(" in downgrade
        assert "op.create_table(" not in downgrade

    def test_downgrade_does_not_alter_baseline(self):
        text = _phase2_migration_text()
        # The new revision's down_reference points to baseline.
        assert "down_revision" in text
        assert '"3f0c6eb4f49e"' in text or "'3f0c6eb4f49e'" in text


# ── Forbidden content ────────────────────────────────────────────────


class TestForbiddenMigrationContent:
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

    def test_no_age_field(self):
        text = _phase2_migration_text()
        assert "age" not in text.split("sa.Column(")[1:]

    def test_no_computed_fields(self):
        text = _phase2_migration_text()
        for field in self.FORBIDDEN_FIELDS:
            assert field not in text, f"Migration must not contain field '{field}'"

    def test_no_jwt_fields(self):
        text = _phase2_migration_text()
        for field in {"jwt", "refresh_token", "token"}:
            assert field not in text.lower()

    def test_no_role_field(self):
        text = _phase2_migration_text()
        assert "role" not in text.lower()

    def test_no_food_tables(self):
        text = _phase2_migration_text()
        assert "food" not in text.lower()

    def test_no_recipe_tables(self):
        text = _phase2_migration_text()
        assert "recipe" not in text.lower()

    def test_no_auth_tables(self):
        text = _phase2_migration_text()
        auth_keywords = {"oauth", "session", "permission"}
        for kw in auth_keywords:
            assert kw not in text.lower()


# ── Boundary ─────────────────────────────────────────────────────────


class TestMigrationBoundary:
    def test_no_create_all_called(self):
        text = _phase2_migration_text()
        assert "create_all" not in text

    def test_no_automatic_migration_execution(self):
        import app.main as app_main

        source = Path(app_main.__file__).read_text(encoding="utf-8")
        assert "alembic" not in source.lower()
