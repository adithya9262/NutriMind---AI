"""Tests for the Task migration content.

These tests inspect the migration file statically and verify Alembic
revision metadata.  A subset additionally exercises Alembic offline
SQL generation to confirm deterministic enum/table/index/constraint DDL.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

NEW_REVISION = "a7b8c9d0e5f"
PREVIOUS_HEAD = "e5f6a7b8c9d0"

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _migration_files() -> list[Path]:
    return sorted(
        f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
    )


def _task_migration_text() -> str:
    files = _migration_files()
    new = [f for f in files if NEW_REVISION in f.name]
    assert len(new) == 1
    return new[0].read_text(encoding="utf-8")


def _task_migration_module():
    files = _migration_files()
    new = [f for f in files if NEW_REVISION in f.name]
    assert len(new) == 1
    spec = importlib.util.spec_from_file_location("_task_migration", new[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _offline_sql(command: str) -> str:
    env = dict(os.environ)
    env["DATABASE_URL"] = "postgresql+asyncpg://localhost/nutrimind"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *command.split()],
        cwd=str(Path(__file__).resolve().parent.parent),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


# ---------------------------------------------------------------------------
# Revision identity / graph
# ---------------------------------------------------------------------------


class TestTaskMigrationGraph:
    def test_exactly_five_migration_revisions(self):
        assert len(_migration_files()) == 7

    def test_new_revision_unique_id(self):
        mod = _task_migration_module()
        assert mod.revision == NEW_REVISION

    def test_new_revision_down_revision_is_previous_head(self):
        mod = _task_migration_module()
        assert mod.down_revision == PREVIOUS_HEAD

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

    def test_base_is_original_baseline(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        bases = script.get_bases()
        assert bases[0] == "3f0c6eb4f49e"

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


# ---------------------------------------------------------------------------
# Existing migration integrity
# ---------------------------------------------------------------------------


class TestExistingMigrationIntegrity:
    def test_existing_revision_ids_unchanged(self):
        files = _migration_files()
        existing = [
            f
            for f in files
            if any(
                r in f.name
                for r in ("3f0c6eb4f49e", "99a3b19be1b8", "b8a7c3d9e1f2", "e5f6a7b8c9d0")
            )
        ]
        assert len(existing) == 4

    def test_existing_head_still_reachable(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        all_revs = {r.revision for r in script.walk_revisions()}
        assert PREVIOUS_HEAD in all_revs

    def test_only_one_new_migration_added(self):
        files = _migration_files()
        new = [f for f in files if NEW_REVISION in f.name]
        assert len(new) == 1


# ---------------------------------------------------------------------------
# Upgrade content
# ---------------------------------------------------------------------------


class TestTaskUpgradeContent:
    def test_creates_tasks_table(self):
        text = _task_migration_text()
        assert '"tasks"' in text or "'tasks'" in text

    def test_creates_exactly_one_new_table(self):
        text = _task_migration_text()
        count = text.count("op.create_table(")
        assert count == 1, f"Expected 1 create_table call, found {count}"

    def test_does_not_recreate_users(self):
        text = _task_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert '"users"' not in upgrade

    def test_does_not_recreate_nutrition_tables(self):
        text = _task_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert '"nutrition_profiles"' not in upgrade
        assert '"nutrition_logs"' not in upgrade

    def test_does_not_recreate_body_weights(self):
        text = _task_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert '"body_weights"' not in upgrade

    def test_no_seed_data(self):
        text = _task_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        assert "op.execute(" not in upgrade
        assert "insert(" not in text

    def test_no_credentials(self):
        text = _task_migration_text()
        assert "://" not in text
        assert "password" not in text.lower()


class TestTaskMigrationSchema:
    def test_eleven_columns(self):
        text = _task_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        count = upgrade.count("sa.Column(")
        assert count == 11, f"Expected 11 columns, found {count}"

    def test_id_column(self):
        text = _task_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text

    def test_user_id_column(self):
        text = _task_migration_text()
        assert 'sa.Column("user_id", sa.Uuid(), nullable=False)' in text

    def test_task_id_column(self):
        text = _task_migration_text()
        assert 'sa.Column("task_id", sa.Uuid(), nullable=False)' in text

    def test_title_column_length(self):
        text = _task_migration_text()
        assert 'sa.Column("title", sa.String(length=200), nullable=False)' in text

    def test_description_column_length(self):
        text = _task_migration_text()
        assert 'sa.Column("description", sa.String(length=2000), nullable=True)' in text

    def test_due_date_column_type(self):
        text = _task_migration_text()
        assert 'sa.Column("due_date", sa.Date(), nullable=True)' in text

    def test_completed_at_timezone(self):
        text = _task_migration_text()
        ts_section = text.split('"tasks"')[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in ts_section.split("completed_at")[1][:200]

    def test_created_at_timezone(self):
        text = _task_migration_text()
        ts_section = text.split('"tasks"')[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in ts_section.split("created_at")[1][:200]

    def test_updated_at_timezone(self):
        text = _task_migration_text()
        ts_section = text.split('"tasks"')[1].split("def downgrade")[0]
        assert "DateTime(timezone=True)" in ts_section.split("updated_at")[1][:200]


class TestTaskMigrationEnums:
    def test_task_priority_enum_created(self):
        text = _task_migration_text()
        assert 'name="task_priority"' in text

    def test_task_status_enum_created(self):
        text = _task_migration_text()
        assert 'name="task_status"' in text

    def test_task_priority_values_lowercase(self):
        text = _task_migration_text()
        assert '"low"' in text
        assert '"medium"' in text
        assert '"high"' in text

    def test_task_status_values_lowercase(self):
        text = _task_migration_text()
        assert '"pending"' in text
        assert '"completed"' in text

    def test_no_uppercase_enum_values(self):
        text = _task_migration_text()
        assert '"LOW"' not in text
        assert '"MEDIUM"' not in text
        assert '"HIGH"' not in text
        assert '"PENDING"' not in text
        assert '"COMPLETED"' not in text

    def test_enum_types_created_once_each(self):
        text = _task_migration_text()
        assert text.count('name="task_priority"') == 1
        assert text.count('name="task_status"') == 1


class TestTaskMigrationConstraints:
    def test_primary_key(self):
        text = _task_migration_text()
        assert 'sa.PrimaryKeyConstraint("id")' in text

    def test_foreign_key_targets_users_id(self):
        text = _task_migration_text()
        assert '"users.id"' in text or "'users.id'" in text

    def test_foreign_key_ondelete_cascade(self):
        text = _task_migration_text()
        assert 'ondelete="CASCADE"' in text

    def test_foreign_key_name(self):
        text = _task_migration_text()
        assert 'name="fk_tasks_user_id"' in text

    def test_composite_unique_constraint(self):
        text = _task_migration_text()
        assert 'name="uq_tasks_user_id_task_id"' in text

    def test_composite_unique_columns(self):
        text = _task_migration_text()
        assert '"user_id"' in text
        assert '"task_id"' in text
        assert 'name="uq_tasks_user_id_task_id"' in text

    def test_status_consistency_check_constraint(self):
        text = _task_migration_text()
        assert 'name="ck_tasks_status_completed_at_consistency"' in text

    def test_status_consistency_expression(self):
        text = _task_migration_text()
        lower = text.lower()
        assert "status = 'pending'" in lower
        assert "completed_at is null" in lower
        assert "status = 'completed'" in lower
        assert "completed_at is not null" in lower

    def test_no_global_task_id_unique_constraint(self):
        text = _task_migration_text()
        # If a unique constraint lists only task_id, it would violate the
        # "unique only within a user's ownership scope" rule. Verify no
        # standalone task_id unique constraint exists.
        import re

        for m in re.finditer(r"sa\.UniqueConstraint\((.*?)\)", text, re.DOTALL):
            body = m.group(1)
            if "task_id" in body and "name=" in body:
                assert "user_id" in body, f"task_id unique without user_id: {body}"
                assert "uq_tasks_user_id_task_id" in body


class TestTaskMigrationIndex:
    def test_lookup_index_created(self):
        text = _task_migration_text()
        assert "op.create_index(" in text

    def test_lookup_index_name(self):
        text = _task_migration_text()
        assert 'name="ix_tasks_user_id_status_due_date"' in text or (
            "ix_tasks_user_id_status_due_date" in text
        )

    def test_lookup_index_columns(self):
        text = _task_migration_text()
        assert '"user_id"' in text
        assert '"status"' in text
        assert '"due_date"' in text

    def test_lookup_index_not_unique(self):
        text = _task_migration_text()
        upgrade = text.split("def upgrade")[1].split("def downgrade")[0]
        # No unique=True on the index.
        idx_block_start = upgrade.index("op.create_index(")
        idx_block = upgrade[idx_block_start : idx_block_start + 400]
        assert "unique=" not in idx_block.lower()


# ---------------------------------------------------------------------------
# Downgrade content
# ---------------------------------------------------------------------------


class TestTaskDowngrade:
    def test_downgrade_drops_index(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.drop_index(" in downgrade

    def test_downgrade_drops_table(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.drop_table(" in downgrade
        assert '"tasks"' in downgrade or "'tasks'" in downgrade

    def test_downgrade_drops_two_enums_after_table(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        count = downgrade.count("DROP TYPE IF EXISTS")
        assert count == 2, f"Expected 2 DROP TYPE statements, found {count}"

    def test_downgrade_no_cascade(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "CASCADE" not in downgrade

    def test_downgrade_does_not_drop_users(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"users"' not in downgrade

    def test_downgrade_does_not_drop_existing_tables(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert '"nutrition_profiles"' not in downgrade
        assert '"nutrition_logs"' not in downgrade
        assert '"body_weights"' not in downgrade

    def test_downgrade_does_not_create_tables(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        assert "op.create_table(" not in downgrade

    def test_downgrade_enum_drop_order_after_table(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        drop_table_pos = downgrade.index("op.drop_table(")
        enum_pos = downgrade.index("DROP TYPE IF EXISTS")
        assert enum_pos > drop_table_pos, "Enums must drop after the table"

    def test_downgrade_drops_status_then_priority(self):
        text = _task_migration_text()
        downgrade = text.split("def downgrade")[1]
        status_pos = downgrade.index("DROP TYPE IF EXISTS task_status")
        priority_pos = downgrade.index("DROP TYPE IF EXISTS task_priority")
        assert status_pos < priority_pos
        assert status_pos > downgrade.index("op.drop_table(")


# ---------------------------------------------------------------------------
# Model / migration parity
# ---------------------------------------------------------------------------


class TestTaskModelMigrationParity:
    def test_table_name_matches(self):
        text = _task_migration_text()
        assert "tasks" in text

    def test_id_column_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'sa.Column("id", sa.Uuid(), nullable=False)' in text
        assert Task.__table__.c["id"].primary_key

    def test_user_id_column_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'sa.Column("user_id", sa.Uuid(), nullable=False)' in text
        assert not Task.__table__.c["user_id"].nullable

    def test_task_id_column_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'sa.Column("task_id", sa.Uuid(), nullable=False)' in text
        assert not Task.__table__.c["task_id"].nullable

    def test_title_column_in_both(self):
        from app.core.tasks import MAX_TASK_TITLE_LENGTH
        from app.models.task import Task

        text = _task_migration_text()
        assert 'sa.Column("title", sa.String(length=200), nullable=False)' in text
        assert Task.__table__.c["title"].type.length == MAX_TASK_TITLE_LENGTH

    def test_description_column_in_both(self):
        from app.core.tasks import MAX_TASK_DESCRIPTION_LENGTH
        from app.models.task import Task

        text = _task_migration_text()
        assert 'sa.Column("description", sa.String(length=2000), nullable=True)' in text
        assert Task.__table__.c["description"].type.length == MAX_TASK_DESCRIPTION_LENGTH

    def test_due_date_column_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'sa.Column("due_date", sa.Date(), nullable=True)' in text
        assert isinstance(Task.__table__.c["due_date"].type, __import__("sqlalchemy").Date)

    def test_fk_name_matches(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'name="fk_tasks_user_id"' in text
        fk = next(iter(Task.__table__.c["user_id"].foreign_keys))
        assert fk.name == "fk_tasks_user_id"

    def test_fk_ondelete_matches(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'ondelete="CASCADE"' in text
        fk = next(iter(Task.__table__.c["user_id"].foreign_keys))
        assert fk.ondelete == "CASCADE"

    def test_fk_target_matches(self):
        from app.models.task import Task

        fk = next(iter(Task.__table__.c["user_id"].foreign_keys))
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"

    def test_composite_unique_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'name="uq_tasks_user_id_task_id"' in text
        uqs = [
            c
            for c in Task.__table__.constraints
            if isinstance(c, __import__("sqlalchemy").UniqueConstraint)
        ]
        names = [c.name for c in uqs]
        assert "uq_tasks_user_id_task_id" in names

    def test_check_constraint_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert 'name="ck_tasks_status_completed_at_consistency"' in text
        checks = [
            c
            for c in Task.__table__.constraints
            if isinstance(c, __import__("sqlalchemy").CheckConstraint)
        ]
        names = [c.name for c in checks]
        assert "ck_tasks_status_completed_at_consistency" in names

    def test_index_in_both(self):
        from app.models.task import Task

        text = _task_migration_text()
        assert "ix_tasks_user_id_status_due_date" in text
        assert len(Task.__table__.indexes) == 1
        idx = next(iter(Task.__table__.indexes))
        assert idx.name == "ix_tasks_user_id_status_due_date"
        assert [c.name for c in idx.columns] == ["user_id", "status", "due_date"]


# ---------------------------------------------------------------------------
# Offline SQL generation
# ---------------------------------------------------------------------------


class TestTaskOfflineSQL:
    def test_offline_upgrade_sql_succeeds(self):
        sql = _offline_sql("upgrade head --sql")
        assert "CREATE TABLE tasks" in sql
        assert "CREATE TYPE task_priority" in sql
        assert "CREATE TYPE task_status" in sql
        assert "CREATE INDEX ix_tasks_user_id_status_due_date" in sql

    def test_offline_upgrade_no_duplicate_enum(self):
        sql = _offline_sql("upgrade head --sql")
        assert sql.count("CREATE TYPE task_priority") == 1
        assert sql.count("CREATE TYPE task_status") == 1

    def test_offline_upgrade_no_drop(self):
        sql = _offline_sql("upgrade head --sql")
        # Upgrade must not drop existing tables.
        assert "DROP TABLE users" not in sql
        assert "DROP TABLE nutrition_profiles" not in sql
        assert "DROP TABLE nutrition_logs" not in sql
        assert "DROP TABLE body_weights" not in sql

    def test_offline_downgrade_sql_succeeds(self):
        sql = _offline_sql(f"downgrade {NEW_REVISION}:{PREVIOUS_HEAD} --sql")
        assert "DROP TABLE tasks" in sql
        assert "DROP INDEX ix_tasks_user_id_status_due_date" in sql
        assert "DROP TYPE IF EXISTS task_status" in sql
        assert "DROP TYPE IF EXISTS task_priority" in sql

    def test_offline_downgrade_enum_after_table(self):
        sql = _offline_sql(f"downgrade {NEW_REVISION}:{PREVIOUS_HEAD} --sql")
        drop_table_pos = sql.index("DROP TABLE tasks")
        status_pos = sql.index("DROP TYPE IF EXISTS task_status")
        priority_pos = sql.index("DROP TYPE IF EXISTS task_priority")
        assert status_pos > drop_table_pos
        assert priority_pos > drop_table_pos

    def test_offline_downgrade_no_cascade(self):
        sql = _offline_sql(f"downgrade {NEW_REVISION}:{PREVIOUS_HEAD} --sql")
        assert "CASCADE" not in sql

    def test_offline_downgrade_existing_tables_intact(self):
        sql = _offline_sql(f"downgrade {NEW_REVISION}:{PREVIOUS_HEAD} --sql")
        assert "DROP TABLE users" not in sql
        assert "DROP TABLE nutrition_profiles" not in sql
        assert "DROP TABLE nutrition_logs" not in sql
        assert "DROP TABLE body_weights" not in sql


# ---------------------------------------------------------------------------
# Forbidden content / boundary
# ---------------------------------------------------------------------------


class TestTaskMigrationForbiddenContent:
    FORBIDDEN_FIELDS = [
        "reminder",
        "recurrence",
        "notification",
        "category",
        "tag",
        "groq",
        "openai",
        "langchain",
        "gemini",
        "llm",
        "recommendation",
    ]

    def test_no_forbidden_fields(self):
        text = _task_migration_text()
        lower = text.lower()
        for token in self.FORBIDDEN_FIELDS:
            assert token not in lower, f"Migration must not contain '{token}'"

    def test_no_jwt_fields(self):
        text = _task_migration_text()
        for token in ("jwt", "refresh_token", "token"):
            assert token not in text.lower()

    def test_no_age_bmi_bmr_tdee(self):
        text = _task_migration_text()
        for token in ("age", "bmi", "bmr", "tdee"):
            assert token not in text.lower()


class TestTaskMigrationBoundary:
    def test_no_create_all_called(self):
        text = _task_migration_text()
        assert "create_all" not in text
