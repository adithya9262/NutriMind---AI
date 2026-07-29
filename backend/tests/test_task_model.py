"""Tests for the Task ORM model.

These tests inspect SQLAlchemy metadata only. They do not connect to a
database, create physical tables, or run migrations.
"""

from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

from app.core.tasks import TaskPriority, TaskStatus
from app.db.base import Base
from app.models import Task, User
from app.models.task import Task as TaskFromModule

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


class TestTaskModelIdentity:
    def test_task_exists(self):
        assert Task is not None

    def test_task_is_base_subclass(self):
        assert issubclass(Task, Base)

    def test_task_uses_timestamp_mixin(self):
        assert issubclass(Task, object)  # structural
        assert hasattr(Task, "created_at")
        assert hasattr(Task, "updated_at")

    def test_tablename(self):
        assert Task.__tablename__ == "tasks"

    def test_exported_from_app_models(self):
        from app.models import Task as Exported

        assert Exported is Task

    def test_single_task_orm_implementation(self):
        # There must be exactly one Task ORM class; no plural "Tasks" model.
        assert Task is TaskFromModule
        assert not hasattr(__import__("app.models", fromlist=["x"]), "Tasks")


class TestTaskMetadata:
    def test_tasks_table_registered(self):
        assert "tasks" in Base.metadata.tables

    def test_exactly_five_tables(self):
        registered = set(Base.metadata.tables.keys())
        assert len(registered) == 6, f"Expected 6 tables, got {registered}"

    def test_exact_table_names(self):
        registered = set(Base.metadata.tables.keys())
        expected = {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }
        assert registered == expected, f"Expected {expected}, got {registered}"

    def test_existing_tables_unchanged(self):
        for name in ("users", "nutrition_profiles", "nutrition_logs", "body_weights"):
            assert name in Base.metadata.tables


class TestTaskExactColumns:
    def test_exact_column_set(self):
        columns = set(Task.__table__.c.keys())
        expected = {
            "id",
            "user_id",
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
            "created_at",
            "updated_at",
        }
        assert columns == expected, f"Expected {expected}, got {columns}"

    def test_no_extra_columns(self):
        columns = set(Task.__table__.c.keys())
        forbidden = {"age", "bmi", "reminder", "tag"}
        for f in forbidden:
            assert f not in columns


class TestTaskIdColumn:
    def test_id_uuid_type(self):
        col = Task.__table__.c["id"]
        assert isinstance(col.type, sa.Uuid)

    def test_id_primary_key(self):
        col = Task.__table__.c["id"]
        assert col.primary_key

    def test_id_non_null(self):
        col = Task.__table__.c["id"]
        assert not col.nullable

    def test_id_default_is_callable(self):
        default = Task.__table__.c["id"].default
        assert default is not None
        val = default.arg(None)
        assert isinstance(val, UUID)


class TestTaskUserIdColumn:
    def test_user_id_uuid_type(self):
        col = Task.__table__.c["user_id"]
        assert isinstance(col.type, sa.Uuid)

    def test_user_id_non_null(self):
        col = Task.__table__.c["user_id"]
        assert not col.nullable

    def test_user_id_foreign_key(self):
        col = Task.__table__.c["user_id"]
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "users"
        assert fks[0].column.name == "id"

    def test_user_id_foreign_key_name(self):
        col = Task.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.name == "fk_tasks_user_id"

    def test_user_id_ondelete_cascade(self):
        col = Task.__table__.c["user_id"]
        fk = next(iter(col.foreign_keys))
        assert fk.ondelete == "CASCADE"


class TestTaskCallerOwnedId:
    def test_task_id_uuid_type(self):
        col = Task.__table__.c["task_id"]
        assert isinstance(col.type, sa.Uuid)

    def test_task_id_non_null(self):
        col = Task.__table__.c["task_id"]
        assert not col.nullable

    def test_task_id_not_primary_key(self):
        col = Task.__table__.c["task_id"]
        assert not col.primary_key

    def test_task_id_no_default(self):
        col = Task.__table__.c["task_id"]
        assert col.default is None
        assert col.server_default is None

    def test_task_id_not_globally_unique(self):
        col = Task.__table__.c["task_id"]
        assert not col.unique


class TestTaskTitleColumn:
    def test_title_string_type(self):
        col = Task.__table__.c["title"]
        assert isinstance(col.type, sa.String)

    def test_title_length_matches_constant(self):
        from app.core.tasks import MAX_TASK_TITLE_LENGTH

        col = Task.__table__.c["title"]
        assert col.type.length == MAX_TASK_TITLE_LENGTH

    def test_title_non_null(self):
        col = Task.__table__.c["title"]
        assert not col.nullable


class TestTaskDescriptionColumn:
    def test_description_string_type(self):
        col = Task.__table__.c["description"]
        assert isinstance(col.type, sa.String)

    def test_description_length_matches_constant(self):
        from app.core.tasks import MAX_TASK_DESCRIPTION_LENGTH

        col = Task.__table__.c["description"]
        assert col.type.length == MAX_TASK_DESCRIPTION_LENGTH

    def test_description_nullable(self):
        col = Task.__table__.c["description"]
        assert col.nullable is True


class TestTaskPriorityColumn:
    def test_priority_reuses_domain_enum(self):
        col = Task.__table__.c["priority"]
        assert col.type.enum_class is TaskPriority

    def test_priority_non_null(self):
        col = Task.__table__.c["priority"]
        assert not col.nullable

    def test_priority_postgres_enum_name(self):
        col = Task.__table__.c["priority"]
        assert col.type.name == "task_priority"

    def test_priority_values_callable_persists_lowercase(self):
        col = Task.__table__.c["priority"]
        assert col.type.values_callable is not None
        result = col.type.values_callable(TaskPriority)
        assert set(result) == {"low", "medium", "high"}
        for member in TaskPriority:
            assert member.name not in result

    def test_priority_no_uppercase_persistence(self):
        col = Task.__table__.c["priority"]
        result = col.type.values_callable(TaskPriority)
        assert "LOW" not in result
        assert "MEDIUM" not in result
        assert "HIGH" not in result


class TestTaskStatusColumn:
    def test_status_reuses_domain_enum(self):
        col = Task.__table__.c["status"]
        assert col.type.enum_class is TaskStatus

    def test_status_non_null(self):
        col = Task.__table__.c["status"]
        assert not col.nullable

    def test_status_postgres_enum_name(self):
        col = Task.__table__.c["status"]
        assert col.type.name == "task_status"

    def test_status_values_callable_persists_lowercase(self):
        col = Task.__table__.c["status"]
        assert col.type.values_callable is not None
        result = col.type.values_callable(TaskStatus)
        assert set(result) == {"pending", "completed"}
        for member in TaskStatus:
            assert member.name not in result

    def test_status_no_uppercase_persistence(self):
        col = Task.__table__.c["status"]
        result = col.type.values_callable(TaskStatus)
        assert "PENDING" not in result
        assert "COMPLETED" not in result


class TestTaskDueDateColumn:
    def test_due_date_sql_date_type(self):
        col = Task.__table__.c["due_date"]
        assert isinstance(col.type, sa.Date)

    def test_due_date_nullable(self):
        col = Task.__table__.c["due_date"]
        assert col.nullable is True

    def test_due_date_no_python_default(self):
        col = Task.__table__.c["due_date"]
        assert col.default is None

    def test_due_date_no_server_default(self):
        col = Task.__table__.c["due_date"]
        assert col.server_default is None


class TestTaskCompletedAtColumn:
    def test_completed_at_datetime_type(self):
        col = Task.__table__.c["completed_at"]
        assert isinstance(col.type, sa.DateTime)

    def test_completed_at_timezone_true(self):
        col = Task.__table__.c["completed_at"]
        assert col.type.timezone is True

    def test_completed_at_nullable(self):
        col = Task.__table__.c["completed_at"]
        assert col.nullable is True

    def test_completed_at_no_python_default(self):
        col = Task.__table__.c["completed_at"]
        assert col.default is None

    def test_completed_at_no_server_default(self):
        col = Task.__table__.c["completed_at"]
        assert col.server_default is None


class TestTaskTimestamps:
    def test_created_at_present(self):
        assert "created_at" in Task.__table__.c

    def test_updated_at_present(self):
        assert "updated_at" in Task.__table__.c

    def test_timestamps_not_redefined_on_task(self):
        # TimestampMixin provides them; Task must not declare new mapped columns
        # named created_at/updated_at beyond the mixin inheritance.
        mapper = sa_inspect(Task)
        created_prop = mapper.columns["created_at"]
        updated_prop = mapper.columns["updated_at"]
        assert created_prop is not None
        assert updated_prop is not None

    def test_timestamps_timezone_true(self):
        assert Task.__table__.c["created_at"].type.timezone is True
        assert Task.__table__.c["updated_at"].type.timezone is True


class TestTaskConstraints:
    def test_primary_key_constraint_present(self):
        pks = [c for c in Task.__table__.constraints if isinstance(c, sa.PrimaryKeyConstraint)]
        assert len(pks) == 1

    def test_named_foreign_key_constraint(self):
        fks = [c for c in Task.__table__.constraints if isinstance(c, sa.ForeignKeyConstraint)]
        names = [c.name for c in fks]
        assert "fk_tasks_user_id" in names

    def test_composite_unique_constraint(self):
        uqs = [c for c in Task.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        target = None
        for uq in uqs:
            if uq.name == "uq_tasks_user_id_task_id":
                target = uq
                break
        assert target is not None, "Composite unique constraint not found"
        cols = [col.name for col in target.columns]
        assert cols == ["user_id", "task_id"]

    def test_no_global_task_id_unique(self):
        uqs = [c for c in Task.__table__.constraints if isinstance(c, sa.UniqueConstraint)]
        for uq in uqs:
            col_names = [col.name for col in uq.columns]
            if "task_id" in col_names:
                # If task_id appears, it must be paired with user_id, never alone.
                assert col_names == ["user_id", "task_id"], (
                    f"task_id must not be globally unique: {col_names}"
                )

    def test_status_consistency_check_constraint(self):
        checks = [c for c in Task.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        names = [c.name for c in checks]
        assert "ck_tasks_status_completed_at_consistency" in names

    def test_check_constraint_exact_logical_behavior(self):
        checks = [
            c
            for c in Task.__table__.constraints
            if isinstance(c, sa.CheckConstraint)
            and c.name == "ck_tasks_status_completed_at_consistency"
        ]
        assert len(checks) == 1
        sql_text = str(checks[0].sqltext).lower()
        # Pending requires completed_at IS NULL.
        assert "pending" in sql_text
        assert "completed_at is null" in sql_text
        # Completed requires completed_at IS NOT NULL.
        assert "completed" in sql_text
        assert "completed_at is not null" in sql_text
        # Logical OR of the two branches.
        assert " or " in sql_text


class TestTaskIndex:
    def test_exactly_one_lookup_index(self):
        indexes = list(Task.__table__.indexes)
        assert len(indexes) == 1, f"Expected 1 index, found {len(indexes)}"

    def test_lookup_index_name(self):
        indexes = {idx.name: idx for idx in Task.__table__.indexes}
        assert "ix_tasks_user_id_status_due_date" in indexes

    def test_lookup_index_column_order(self):
        for idx in Task.__table__.indexes:
            if idx.name == "ix_tasks_user_id_status_due_date":
                cols = [col.name for col in idx.columns]
                assert cols == ["user_id", "status", "due_date"]
                return
        raise AssertionError("Lookup index not found")

    def test_lookup_index_non_unique(self):
        for idx in Task.__table__.indexes:
            if idx.name == "ix_tasks_user_id_status_due_date":
                assert idx.unique is False
                return
        raise AssertionError("Lookup index not found")

    def test_no_redundant_indexes(self):
        expected = {"ix_tasks_user_id_status_due_date"}
        actual = {idx.name for idx in Task.__table__.indexes}
        assert actual == expected, f"Expected {expected}, got {actual}"


class TestTaskRelationships:
    def test_user_tasks_relationship_exists(self):
        assert "tasks" in User.__mapper__.relationships

    def test_task_user_relationship_exists(self):
        assert "user" in Task.__mapper__.relationships

    def test_back_populates_symmetric(self):
        user_rel = User.__mapper__.relationships["tasks"]
        task_rel = Task.__mapper__.relationships["user"]
        assert user_rel.back_populates == "user"
        assert task_rel.back_populates == "tasks"

    def test_user_tasks_cascade_all_delete_orphan(self):
        rel = User.__mapper__.relationships["tasks"]
        assert rel.uselist is True
        assert rel.cascade.delete_orphan is True
        assert rel.cascade.delete is True

    def test_user_tasks_mapper_class(self):
        rel = User.__mapper__.relationships["tasks"]
        assert rel.mapper.class_ is Task

    def test_task_user_mapper_class(self):
        rel = Task.__mapper__.relationships["user"]
        assert rel.mapper.class_ is User

    def test_existing_user_relationships_unchanged(self):
        rel_names = set(User.__mapper__.relationships.keys())
        for name in ("nutrition_profile", "nutrition_logs", "body_weights", "tasks"):
            assert name in rel_names

    def test_existing_user_relationships_back_populates(self):
        assert User.__mapper__.relationships["nutrition_profile"].back_populates == "user"
        assert User.__mapper__.relationships["nutrition_logs"].back_populates == "user"
        assert User.__mapper__.relationships["body_weights"].back_populates == "user"

    def test_existing_user_relationships_cascade(self):
        for name in ("nutrition_profile", "nutrition_logs", "body_weights"):
            rel = User.__mapper__.relationships[name]
            assert rel.cascade.delete_orphan is True
            assert rel.cascade.delete is True


class TestTaskInstanceBehavior:
    def _uuid(self) -> UUID:
        return UUID("12345678-1234-5678-1234-567812345678")

    def test_valid_pending_instance(self):
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="Buy groceries",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
        )
        assert t.status is TaskStatus.PENDING
        assert t.completed_at is None

    def test_valid_completed_instance(self):
        from datetime import datetime

        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="Buy groceries",
            priority=TaskPriority.HIGH,
            status=TaskStatus.COMPLETED,
            completed_at=datetime(2025, 6, 15, 12, 30, 0),
        )
        assert t.status is TaskStatus.COMPLETED
        assert t.completed_at == datetime(2025, 6, 15, 12, 30, 0)

    def test_optional_description(self):
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="T",
            description=None,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
        )
        assert t.description is None

    def test_optional_due_date(self):
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="T",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=None,
        )
        assert t.due_date is None

    def test_caller_owned_task_id_preserved(self):
        owned = UUID("87654321-4321-8765-4321-876543218765")
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=owned,
            title="T",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
        )
        assert t.task_id == owned

    def test_domain_enum_assignment(self):
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="T",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
        )
        assert t.priority is TaskPriority.HIGH

    def test_due_date_not_auto_assigned(self):
        from datetime import date

        provided = date(2030, 1, 1)
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="T",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=provided,
        )
        assert t.due_date == provided

    def test_completed_at_not_auto_assigned(self):
        from datetime import datetime

        provided = datetime(2025, 6, 15, 12, 30, 0)
        t = Task(
            id=self._uuid(),
            user_id=self._uuid(),
            task_id=self._uuid(),
            title="T",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.COMPLETED,
            completed_at=provided,
        )
        assert t.completed_at == provided
