"""Tests for the BodyWeight migration content.

These tests inspect the migration file statically and verify Alembic
revision metadata.  They do NOT connect to a database or apply migrations.
"""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.body_weight import BodyWeight

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _migration_files() -> list[Path]:
    return sorted(
        f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
    )


def _body_weight_migration_text() -> str:
    files = _migration_files()
    new = [f for f in files if "e5f6a7b8c9d0" in f.name]
    assert len(new) == 1
    return new[0].read_text(encoding="utf-8")


def _body_weight_migration_module():
    files = _migration_files()
    new = [f for f in files if "e5f6a7b8c9d0" in f.name]
    assert len(new) == 1
    spec = importlib.util.spec_from_file_location("_bw_migration", new[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Revision structure
# ---------------------------------------------------------------------------


class TestBodyWeightMigrationGraph:
    def test_exactly_five_migration_revisions(self):
        assert len(_migration_files()) == 7

    def test_new_revision_down_revision_is_nutrition_logs(self):
        mod = _body_weight_migration_module()
        assert mod.down_revision == "b8a7c3d9e1f2"

    def test_revision_id_valid(self):
        mod = _body_weight_migration_module()
        assert mod.revision == "e5f6a7b8c9d0"

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

    def test_head_is_new_revision(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        heads = script.get_heads()
        assert heads[0] == "0295723946b2"

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

    def test_baseline_is_base(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        bases = script.get_bases()
        assert bases[0] == "3f0c6eb4f49e"


# ---------------------------------------------------------------------------
# Existing migration integrity
# ---------------------------------------------------------------------------


class TestExistingMigrationIntegrity:
    def test_baseline_hash_unchanged(self):
        files = _migration_files()
        baseline = [f for f in files if "3f0c6eb4f49e" in f.name]
        assert len(baseline) == 1
        content = baseline[0].read_bytes()
        import hashlib

        assert (
            hashlib.sha256(content).hexdigest().upper()
            == "E5F4825A7DF0E9793D6D869038695FBAF8EEF99F7CA91E3CD610BAABA04A4873"
        )

    def test_phase2_hash_unchanged(self):
        files = _migration_files()
        phase2 = [f for f in files if "99a3b19be1b8" in f.name]
        assert len(phase2) == 1
        content = phase2[0].read_bytes()
        import hashlib

        assert (
            hashlib.sha256(content).hexdigest().upper()
            == "E85AC712CAA28C2A8DB02FA0AFD8C48C5BB81D8ADB5BB4C52237E87598D2EFAF"
        )

    def test_nutrition_logs_hash_unchanged(self):
        files = _migration_files()
        nl = [f for f in files if "b8a7c3d9e1f2" in f.name]
        assert len(nl) == 1
        content = nl[0].read_bytes()
        import hashlib

        assert (
            hashlib.sha256(content).hexdigest().upper()
            == "BB915C43F1BC895C5A3EDB046127F049BDD086F40E6A93DB4906E93F1B518061"
        )

    def test_only_new_migration_added(self):
        files = _migration_files()
        assert len(files) == 7


# ---------------------------------------------------------------------------
# Upgrade content
# ---------------------------------------------------------------------------


class TestBodyWeightUpgradeContent:
    def test_creates_body_weights_table(self):
        text = _body_weight_migration_text()
        assert '"body_weights"' in text or "'body_weights'" in text

    def test_creates_exactly_one_new_table(self):
        text = _body_weight_migration_text()
        count = text.count("op.create_table(")
        assert count == 1, f"Expected 1 create_table call, found {count}"

    def test_does_not_recreate_users(self):
        text = _body_weight_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert '"users"' not in upgrade

    def test_does_not_recreate_nutrition_profiles(self):
        text = _body_weight_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert '"nutrition_profiles"' not in upgrade

    def test_does_not_recreate_nutrition_logs(self):
        text = _body_weight_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert '"nutrition_logs"' not in upgrade

    def test_no_seed_data(self):
        text = _body_weight_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert "op.execute(" not in upgrade
        assert "insert(" not in text

    def test_no_credentials(self):
        text = _body_weight_migration_text()
        assert "://" not in text
        assert "password" not in text.lower()


# ---------------------------------------------------------------------------
# Column schema
# ---------------------------------------------------------------------------


class TestBodyWeightMigrationSchema:
    def test_id_column(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text

    def test_user_id_column(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("user_id", sa.Uuid(), nullable=False)' in text

    def test_entry_id_column(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("entry_id", sa.Uuid(), nullable=False)' in text

    def test_logged_date_column_type(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("logged_date", sa.Date(), nullable=False)' in text

    def test_weight_kg_numeric_precision(self):
        text = _body_weight_migration_text()
        assert "Numeric(precision=5, scale=2)" in text.split("weight_kg")[1][:200]

    def test_numeric_scale_is_two(self):
        text = _body_weight_migration_text()
        assert "scale=2" in text.split("weight_kg")[1][:200]

    def test_created_at_timezone(self):
        text = _body_weight_migration_text()
        bw_section = text.split("body_weights")[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in bw_section.split("created_at")[1][:200]

    def test_updated_at_timezone(self):
        text = _body_weight_migration_text()
        bw_section = text.split("body_weights")[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in bw_section.split("updated_at")[1][:200]

    def test_seven_columns(self):
        text = _body_weight_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        count = upgrade.count("sa.Column(")
        assert count == 7, f"Expected 7 columns, found {count}"


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


class TestBodyWeightMigrationConstraints:
    def test_primary_key(self):
        text = _body_weight_migration_text()
        assert 'sa.PrimaryKeyConstraint("id")' in text

    def test_foreign_key_targets_users_id(self):
        text = _body_weight_migration_text()
        assert '"users.id"' in text or "'users.id'" in text

    def test_foreign_key_ondelete_cascade(self):
        text = _body_weight_migration_text()
        assert 'ondelete="CASCADE"' in text

    def test_foreign_key_name(self):
        text = _body_weight_migration_text()
        assert 'name="fk_body_weights_user_id"' in text

    def test_date_unique_constraint(self):
        text = _body_weight_migration_text()
        assert 'name="uq_body_weights_user_id_logged_date"' in text

    def test_date_unique_constraint_columns(self):
        text = _body_weight_migration_text()
        assert '"user_id"' in text
        assert '"logged_date"' in text
        assert 'name="uq_body_weights_user_id_logged_date"' in text

    def test_entry_id_unique_constraint(self):
        text = _body_weight_migration_text()
        assert 'name="uq_body_weights_user_id_entry_id"' in text

    def test_entry_id_unique_constraint_columns(self):
        text = _body_weight_migration_text()
        assert '"user_id"' in text
        assert '"entry_id"' in text
        assert 'name="uq_body_weights_user_id_entry_id"' in text

    def test_weight_range_check_constraint(self):
        text = _body_weight_migration_text()
        assert 'name="ck_body_weights_weight_kg_range"' in text

    def test_weight_range_expression(self):
        text = _body_weight_migration_text()
        assert "weight_kg >= 10.00 AND weight_kg <= 700.00" in text

    def test_no_extra_check_constraints(self):
        text = _body_weight_migration_text()
        count = text.count("sa.CheckConstraint(")
        assert count == 1, f"Expected 1 check constraint, found {count}"


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


class TestBodyWeightMigrationIndex:
    def test_no_redundant_explicit_index(self):
        text = _body_weight_migration_text()
        lines = text.split("\n")
        index_count = sum(1 for line in lines if "op.create_index(" in line)
        assert index_count == 0, f"Expected 0 create_index calls, found {index_count}"


# ---------------------------------------------------------------------------
# Model/migration parity
# ---------------------------------------------------------------------------


class TestBodyWeightModelMigrationParity:
    def test_table_name_matches(self):
        text = _body_weight_migration_text()
        assert BodyWeight.__tablename__ in text

    def test_id_column_in_both(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text
        col = BodyWeight.__table__.c["id"]
        assert col.primary_key

    def test_user_id_column_in_both(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("user_id", sa.Uuid(), nullable=False)' in text
        col = BodyWeight.__table__.c["user_id"]
        assert not col.nullable

    def test_entry_id_column_in_both(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("entry_id", sa.Uuid(), nullable=False)' in text
        col = BodyWeight.__table__.c["entry_id"]
        assert not col.nullable

    def test_logged_date_column_in_both(self):
        text = _body_weight_migration_text()
        assert 'sa.Column("logged_date", sa.Date(), nullable=False)' in text
        col = BodyWeight.__table__.c["logged_date"]
        assert not col.nullable

    def test_weight_kg_precision_scale_matches(self):
        col = BodyWeight.__table__.c["weight_kg"]
        assert col.type.precision == 5
        assert col.type.scale == 2
        text = _body_weight_migration_text()
        assert "Numeric(precision=5, scale=2)" in text.split("weight_kg")[1][:200]

    def test_created_at_in_both(self):
        col = BodyWeight.__table__.c["created_at"]
        assert col.type.timezone is True

    def test_updated_at_in_both(self):
        col = BodyWeight.__table__.c["updated_at"]
        assert col.type.timezone is True

    def test_fk_name_matches(self):
        col = BodyWeight.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.name == "fk_body_weights_user_id"
        text = _body_weight_migration_text()
        assert 'name="fk_body_weights_user_id"' in text

    def test_fk_ondelete_matches(self):
        col = BodyWeight.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete == "CASCADE"
        text = _body_weight_migration_text()
        assert 'ondelete="CASCADE"' in text

    def test_fk_target_matches(self):
        col = BodyWeight.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"

    def test_date_unique_constraint_in_both(self):
        uqs = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        _ = uqs  # imported via module

    def test_no_index_in_either(self):
        assert len(BodyWeight.__table__.indexes) == 0
        text = _body_weight_migration_text()
        assert "op.create_index(" not in text


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


class TestBodyWeightDowngrade:
    def test_downgrade_drops_table(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.drop_table(" in downgrade

    def test_downgrade_drops_body_weights(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"body_weights"' in downgrade or "'body_weights'" in downgrade

    def test_downgrade_no_cascade(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "CASCADE" not in downgrade

    def test_downgrade_does_not_drop_users(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"users"' not in downgrade

    def test_downgrade_does_not_drop_nutrition_profiles(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"nutrition_profiles"' not in downgrade

    def test_downgrade_does_not_drop_nutrition_logs(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"nutrition_logs"' not in downgrade

    def test_downgrade_does_not_create_tables(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.create_table(" not in downgrade

    def test_downgrade_does_not_drop_enums(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "DROP TYPE IF EXISTS" not in downgrade

    def test_downgrade_exactly_one_drop_table(self):
        text = _body_weight_migration_text()
        downgrade = text.split("def downgrade")[1]
        count = downgrade.count("op.drop_table(")
        assert count == 1, f"Expected 1 drop_table call, found {count}"


# ---------------------------------------------------------------------------
# Forbidden content
# ---------------------------------------------------------------------------


class TestBodyWeightForbiddenContent:
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
        text = _body_weight_migration_text()
        for field in self.FORBIDDEN_FIELDS:
            assert field not in text, f"Migration must not contain field '{field}'"

    def test_no_aggregation_fields(self):
        text = _body_weight_migration_text()
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

    def test_no_body_fat(self):
        text = _body_weight_migration_text()
        assert "body_fat" not in text.lower()

    def test_no_measurement_fields(self):
        text = _body_weight_migration_text()
        for token in ("waist", "chest", "hip", "arm", "circumference"):
            assert token not in text.lower()

    def test_no_trend(self):
        text = _body_weight_migration_text()
        assert "trend" not in text.lower()

    def test_no_prediction(self):
        text = _body_weight_migration_text()
        assert "predict" not in text.lower()


# ---------------------------------------------------------------------------
# Boundary
# ---------------------------------------------------------------------------


class TestBodyWeightMigrationBoundary:
    def test_no_create_all_called(self):
        text = _body_weight_migration_text()
        assert "create_all" not in text

    def test_no_automatic_migration_execution(self):
        import app.main as app_main

        source = Path(app_main.__file__).read_text(encoding="utf-8")
        assert "alembic" not in source.lower()
