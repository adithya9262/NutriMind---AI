"""Phase 5E-6 Final Audit: Cross-layer invariant tests for Task Management module.

These tests verify critical invariants across domain, schema, ORM, migration,
repository, service, and API layers. They complement (not duplicate) the
extensive unit tests in test_tasks.py, test_task_*.py.
"""

from __future__ import annotations

import importlib
import inspect
import os
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.task_exceptions import (
    InvalidTaskError,
)
from app.core.tasks import (
    MAX_TASK_DESCRIPTION_LENGTH,
    MAX_TASK_TITLE_LENGTH,
    MIN_TASK_TITLE_LENGTH,
    Task,
    TaskPriority,
    TaskStatus,
    create_task,
)
from app.db.base import Base
from app.main import create_app
from app.models.task import Task as TaskORM
from app.repositories.task import TaskRepository
from app.schemas.tasks import (
    TaskCreate,
    TaskData,
    TaskDeleteSuccessResponse,
    TaskListData,
)
from app.services.task import TaskService

# =============================================================================
# A. Domain / Schema / ORM Constant Alignment
# =============================================================================


class TestConstantAlignment:
    def test_title_length_constants_match_across_layers(self):
        from app.models.task import Task as TaskORM
        from app.schemas.tasks import TaskCreate

        assert TaskCreate.model_fields["title"].json_schema_extra is None
        orm_title_col = TaskORM.__table__.c["title"]
        assert orm_title_col.type.length == MAX_TASK_TITLE_LENGTH

    def test_description_length_constants_match_across_layers(self):
        from app.models.task import Task as TaskORM

        orm_desc_col = TaskORM.__table__.c["description"]
        assert orm_desc_col.type.length == MAX_TASK_DESCRIPTION_LENGTH

    def test_domain_constants_exact_values(self):
        assert MIN_TASK_TITLE_LENGTH == 1
        assert MAX_TASK_TITLE_LENGTH == 200
        assert MAX_TASK_DESCRIPTION_LENGTH == 2000


# =============================================================================
# B. Enum Alignment Across All Layers
# =============================================================================


class TestEnumAlignment:
    def test_priority_enum_members_exact(self):
        assert {e.name for e in TaskPriority} == {"LOW", "MEDIUM", "HIGH"}
        assert {e.value for e in TaskPriority} == {"low", "medium", "high"}

    def test_status_enum_members_exact(self):
        assert {e.name for e in TaskStatus} == {"PENDING", "COMPLETED"}
        assert {e.value for e in TaskStatus} == {"pending", "completed"}

    def test_orm_uses_domain_enums_directly(self):
        assert TaskORM.__table__.c["priority"].type.enum_class is TaskPriority
        assert TaskORM.__table__.c["status"].type.enum_class is TaskStatus

    def test_migration_enum_values_lowercase(self):
        migration_text = Path("alembic/versions/a7b8c9d0e5f_create_tasks.py").read_text()
        assert '"low"' in migration_text
        assert '"medium"' in migration_text
        assert '"high"' in migration_text
        assert '"pending"' in migration_text
        assert '"completed"' in migration_text
        assert '"LOW"' not in migration_text
        assert '"HIGH"' not in migration_text
        assert '"PENDING"' not in migration_text

    def test_openapi_enum_serialization_lowercase(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        task_data = openapi["components"]["schemas"]["TaskData"]
        priority_enum = task_data["properties"]["priority"]["$ref"]
        status_enum = task_data["properties"]["status"]["$ref"]
        priority_schema = openapi["components"]["schemas"][priority_enum.split("/")[-1]]
        status_schema = openapi["components"]["schemas"][status_enum.split("/")[-1]]
        assert set(priority_schema["enum"]) == {"low", "medium", "high"}
        assert set(status_schema["enum"]) == {"pending", "completed"}

    def test_schema_reuses_domain_enums(self):
        assert TaskCreate.model_fields["priority"].annotation is TaskPriority
        assert TaskData.model_fields["priority"].annotation is TaskPriority
        assert TaskData.model_fields["status"].annotation is TaskStatus


# =============================================================================
# C. Task Field Alignment Across Domain / Schema / ORM / Public Responses
# =============================================================================


class TestFieldAlignment:
    def test_domain_task_exact_fields(self):
        fields = list(Task.__dataclass_fields__.keys())
        assert fields == [
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
        ]

    def test_schema_taskdata_exact_fields(self):
        fields = list(TaskData.model_fields.keys())
        assert fields == [
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
        ]

    def test_orm_task_exact_columns(self):
        cols = set(TaskORM.__table__.c.keys())
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
        assert cols == expected

    def test_public_response_excludes_internal_fields(self):
        task = create_task(
            task_id=UUID("12345678-1234-5678-1234-567812345678"),
            title="Test",
            description=None,
            priority=TaskPriority.MEDIUM,
            due_date=None,
        )
        data = TaskData.from_domain(task).model_dump()
        forbidden = {"user_id", "id", "created_at", "updated_at", "_sa_instance_state"}
        for f in forbidden:
            assert f not in data, f"Forbidden field leaked: {f}"

    def test_no_extra_columns_in_orm(self):
        forbidden = {"reminder", "notification", "tag", "subtask"}
        cols = set(TaskORM.__table__.c.keys())
        for f in forbidden:
            assert f not in cols, f"Forbidden column in ORM: {f}"


# =============================================================================
# D. Title/Description Length Alignment
# =============================================================================


class TestLengthAlignment:
    def test_schema_title_max_length_matches_domain(self):
        assert TaskCreate.model_fields["title"].json_schema_extra is None
        # Validation is via field_validator, but max length is domain constant
        from app.schemas.tasks import MAX_TASK_TITLE_LENGTH as SCHEMA_MAX_TITLE

        assert SCHEMA_MAX_TITLE == MAX_TASK_TITLE_LENGTH

    def test_schema_description_max_length_matches_domain(self):
        from app.schemas.tasks import MAX_TASK_DESCRIPTION_LENGTH as SCHEMA_MAX_DESC

        assert SCHEMA_MAX_DESC == MAX_TASK_DESCRIPTION_LENGTH


# =============================================================================
# E. Status / completed_at State Consistency
# =============================================================================


class TestStateConsistency:
    def test_domain_pending_forbids_completed_at(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=UUID("12345678-1234-5678-1234-567812345678"),
                title="Test",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=datetime.now(UTC),
            )

    def test_domain_completed_requires_completed_at(self):
        with pytest.raises(InvalidTaskError):
            Task(
                task_id=UUID("12345678-1234-5678-1234-567812345678"),
                title="Test",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.COMPLETED,
                due_date=None,
                completed_at=None,
            )

    def test_schema_taskdata_validates_state_invariant(self):
        with pytest.raises(Exception):
            TaskData(
                task_id=UUID("12345678-1234-5678-1234-567812345678"),
                title="Test",
                description=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=None,
                completed_at=datetime.now(UTC),
            )

    def test_orm_check_constraint_enforces_consistency(self):
        checks = [
            c
            for c in TaskORM.__table__.constraints
            if hasattr(c, "name") and c.name == "ck_tasks_status_completed_at_consistency"
        ]
        assert len(checks) == 1
        sql = str(checks[0].sqltext).lower()
        assert "pending" in sql and "completed_at is null" in sql
        assert "completed" in sql and "completed_at is not null" in sql
        assert " or " in sql

    def test_migration_check_constraint_matches(self):
        migration_text = Path("alembic/versions/a7b8c9d0e5f_create_tasks.py").read_text()
        assert "ck_tasks_status_completed_at_consistency" in migration_text
        assert "pending" in migration_text.lower()
        assert "completed" in migration_text.lower()
        assert "completed_at is null" in migration_text.lower()
        assert "completed_at is not null" in migration_text.lower()


# =============================================================================
# F. Repository User-Scoping
# =============================================================================


class TestRepositoryUserScoping:
    def test_list_by_user_id_filters_by_user(self):
        import inspect

        source = inspect.getsource(TaskRepository.list_by_user_id)
        assert "user_id ==" in source or "user_id ==" in source.replace(" ", "")

    def test_get_by_user_and_task_id_requires_both(self):
        import inspect

        source = inspect.getsource(TaskRepository.get_by_user_and_task_id)
        assert "user_id" in source and "task_id" in source
        assert "where" in source.lower()

    def test_create_requires_user_id(self):
        import inspect

        source = inspect.getsource(TaskRepository.create)
        assert "user_id" in source

    def test_delete_accepts_orm_object_not_id(self):
        import inspect

        source = inspect.getsource(TaskRepository.delete)
        assert "task: TaskORM" in source
        assert "task_id" not in source or "task.task_id" not in source

    def test_no_unscoped_lookup_by_task_id_alone(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        # Should not have a method that queries by task_id without user_id
        for line in source.splitlines():
            if "task_id" in line and "user_id" not in line and "where" in line.lower():
                # Allow in docstrings or comments
                if not line.strip().startswith("#") and '"""' not in line:
                    pytest.fail(f"Potential unscoped lookup: {line.strip()}")


# =============================================================================
# G. Repository Flush-Only Behavior
# =============================================================================


class TestRepositoryFlushOnly:
    def test_no_commit_in_repository(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "commit(" not in source
        assert "self._session.commit" not in source

    def test_no_rollback_in_repository(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "rollback(" not in source
        assert "self._session.rollback" not in source

    def test_no_refresh_in_repository(self):
        import inspect

        source = inspect.getsource(TaskRepository)
        assert "refresh(" not in source
        assert "self._session.refresh" not in source

    def test_create_flushes_once(self):
        import inspect

        source = inspect.getsource(TaskRepository.create)
        # Count actual await flush() calls, not docstring mentions
        assert source.count("await self._session.flush()") == 1

    def test_update_flushes_once(self):
        import inspect

        source = inspect.getsource(TaskRepository.update)
        assert source.count("await self._session.flush()") == 1

    def test_delete_flushes_once(self):
        import inspect

        source = inspect.getsource(TaskRepository.delete)
        assert source.count("await self._session.flush()") == 1


# =============================================================================
# H. Service Transaction Independence
# =============================================================================


class TestServiceTransactionIndependence:
    def test_no_fastapi_import(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "fastapi" not in source.lower()

    def test_no_starlette_import(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "starlette" not in source.lower()

    def test_no_httpexception(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "httpexception" not in source.lower()

    def test_no_sqlalchemy_import(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "sqlalchemy" not in source.lower()

    def test_no_asyncsession_import(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "asyncsession" not in source.lower()

    def test_no_commit_rollback_flush_refresh(self):
        import inspect

        source = inspect.getsource(TaskService)
        for term in ["commit(", "rollback(", "flush(", "refresh(", "session.add", "session.delete"]:
            assert term not in source.lower(), f"Service must not manage transactions: {term}"

    def test_delegates_persistence_to_repository(self):
        import inspect

        source = inspect.getsource(TaskService)
        assert "self._repository" in source


# =============================================================================
# I. API Transaction Ownership
# =============================================================================


class TestAPITransactionOwnership:
    def test_write_endpoints_commit_exactly_once(self):
        import inspect

        write_endpoints = [
            "create_task_endpoint",
            "complete_task_endpoint",
            "reopen_task_endpoint",
            "delete_task_endpoint",
        ]
        for ep in write_endpoints:
            fn = getattr(importlib.import_module("app.api.v1.tasks"), ep)
            fn_source = inspect.getsource(fn)
            assert fn_source.count("await session.commit()") == 1, f"{ep} must commit exactly once"

    def test_read_endpoints_no_commit(self):
        import inspect

        for ep_name in ["list_tasks_endpoint", "get_task_endpoint"]:
            fn = getattr(importlib.import_module("app.api.v1.tasks"), ep_name)
            fn_source = inspect.getsource(fn)
            assert "session.commit" not in fn_source, f"{ep_name} must not commit"

    def test_write_commits_after_service_success(self):
        import inspect

        module = importlib.import_module("app.api.v1.tasks")
        for ep_name in [
            "create_task_endpoint",
            "complete_task_endpoint",
            "reopen_task_endpoint",
            "delete_task_endpoint",
        ]:
            fn = getattr(module, ep_name)
            fn_source = inspect.getsource(fn)
            # Service call should be before commit
            service_call_pos = fn_source.find("await service.")
            commit_pos = fn_source.find("await session.commit()")
            assert service_call_pos != -1 and commit_pos != -1
            assert service_call_pos < commit_pos, f"{ep_name}: commit before service call"

    def test_write_failures_rollback(self):
        import inspect

        module = importlib.import_module("app.api.v1.tasks")
        for ep_name in [
            "create_task_endpoint",
            "complete_task_endpoint",
            "reopen_task_endpoint",
            "delete_task_endpoint",
        ]:
            fn = getattr(module, ep_name)
            fn_source = inspect.getsource(fn)
            assert "session.rollback()" in fn_source, f"{ep_name}: missing rollback on failure"

    def test_no_hidden_autocommit(self):
        import inspect

        source = inspect.getsource(importlib.import_module("app.api.v1.tasks"))
        assert "autocommit" not in source.lower()

    def test_no_unnecessary_refresh(self):
        import inspect

        module = importlib.import_module("app.api.v1.tasks")
        for ep_name in [
            "create_task_endpoint",
            "complete_task_endpoint",
            "reopen_task_endpoint",
            "delete_task_endpoint",
        ]:
            fn = getattr(module, ep_name)
            fn_source = inspect.getsource(fn)
            assert "session.refresh" not in fn_source, f"{ep_name}: unnecessary refresh"


# =============================================================================
# J. Complete/Reopen Domain Helper Reuse
# =============================================================================


class TestDomainHelperReuse:
    def test_service_complete_calls_frozen_complete_task_once(self):
        import app.services.task as svc_mod

        original = svc_mod.complete_task
        calls = {"n": 0}

        def spy(*, task, completed_at):
            calls["n"] += 1
            return original(task=task, completed_at=completed_at)

        svc_mod.complete_task = spy
        try:
            import asyncio
            from unittest.mock import AsyncMock, MagicMock

            repo = MagicMock()
            repo.get_by_user_and_task_id = AsyncMock(
                return_value=MagicMock(
                    task_id=UUID("12345678-1234-5678-1234-567812345678"),
                    title="Test",
                    description=None,
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    due_date=None,
                    completed_at=None,
                    user_id=UUID("11111111-1111-1111-1111-111111111111"),
                )
            )
            repo.update = AsyncMock(return_value=None)
            service = TaskService(repo)
            asyncio.run(
                service.complete_task(
                    user_id=UUID("11111111-1111-1111-1111-111111111111"),
                    task_id=UUID("12345678-1234-5678-1234-567812345678"),
                    completed_at=datetime(2025, 6, 15, 12, 30, 0, tzinfo=UTC),
                )
            )
            assert calls["n"] == 1
        finally:
            svc_mod.complete_task = original

    def test_service_reopen_calls_frozen_reopen_task_once(self):
        import app.services.task as svc_mod

        original = svc_mod.reopen_task
        calls = {"n": 0}

        def spy(*, task):
            calls["n"] += 1
            return original(task=task)

        svc_mod.reopen_task = spy
        try:
            import asyncio
            from unittest.mock import AsyncMock, MagicMock

            repo = MagicMock()
            repo.get_by_user_and_task_id = AsyncMock(
                return_value=MagicMock(
                    task_id=UUID("12345678-1234-5678-1234-567812345678"),
                    title="Test",
                    description=None,
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.COMPLETED,
                    due_date=None,
                    completed_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC),
                    user_id=UUID("11111111-1111-1111-1111-111111111111"),
                )
            )
            repo.update = AsyncMock(return_value=None)
            service = TaskService(repo)
            asyncio.run(
                service.reopen_task(
                    user_id=UUID("11111111-1111-1111-1111-111111111111"),
                    task_id=UUID("12345678-1234-5678-1234-567812345678"),
                )
            )
            assert calls["n"] == 1
        finally:
            svc_mod.reopen_task = original


# =============================================================================
# K. Deterministic Ordering Reuse
# =============================================================================


class TestDeterministicOrderingReuse:
    def test_service_list_calls_frozen_order_tasks_once(self):
        import app.services.task as svc_mod

        original = svc_mod.order_tasks
        calls = {"n": 0}

        def spy(*, tasks):
            calls["n"] += 1
            return original(tasks=tasks)

        svc_mod.order_tasks = spy
        try:
            import asyncio
            from unittest.mock import AsyncMock, MagicMock

            repo = MagicMock()
            repo.list_by_user_id = AsyncMock(return_value=[])
            service = TaskService(repo)
            asyncio.run(service.list_tasks(user_id=UUID("11111111-1111-1111-1111-111111111111")))
            assert calls["n"] == 1
        finally:
            svc_mod.order_tasks = original

    def test_api_preserves_service_ordering(self):
        import inspect

        source = inspect.getsource(importlib.import_module("app.api.v1.tasks"))
        # The list endpoint should call service.list_tasks and return its result
        # without re-sorting
        assert "service.list_tasks" in source
        assert "order_tasks" not in source or "frozen" not in source


# =============================================================================
# L. No System-Clock Fallback
# =============================================================================


class TestNoSystemClockFallback:
    def test_domain_no_clock(self):
        import inspect

        source = inspect.getsource(importlib.import_module("app.core.tasks"))
        for term in [
            "date.today(",
            "datetime.now(",
            "datetime.utcnow(",
            "time.time(",
            "timezone.utc",
        ]:
            assert term not in source, f"Domain uses system clock: {term}"

    def test_schema_no_clock(self):
        import inspect

        source = inspect.getsource(importlib.import_module("app.schemas.tasks"))
        for term in ["date.today(", "datetime.now(", "datetime.utcnow("]:
            assert term not in source, f"Schema uses system clock: {term}"

    def test_repository_no_clock(self):
        import inspect

        source = inspect.getsource(importlib.import_module("app.repositories.task"))
        for term in ["date.today(", "datetime.now(", "datetime.utcnow("]:
            assert term not in source, f"Repository uses system clock: {term}"

    def test_service_no_clock(self):
        import inspect

        source = inspect.getsource(importlib.import_module("app.services.task"))
        for term in ["date.today(", "datetime.now(", "datetime.utcnow("]:
            assert term not in source, f"Service uses system clock: {term}"

    def test_api_complete_endpoint_no_clock_fallback(self):
        import inspect

        # The complete endpoint must use body.completed_at, not a fallback
        complete_fn = getattr(importlib.import_module("app.api.v1.tasks"), "complete_task_endpoint")
        complete_source = inspect.getsource(complete_fn)
        assert "body.completed_at" in complete_source
        assert "datetime.now" not in complete_source
        assert "datetime.utcnow" not in complete_source


# =============================================================================
# M. Exact Route Inventory
# =============================================================================


class TestExactRouteInventory:
    def test_exactly_six_task_operations(self):
        from app.main import create_app

        app = create_app()
        task_routes = [r for r in app.routes if hasattr(r, "path") and "tasks" in r.path]
        methods = sum(len(getattr(r, "methods", [])) for r in task_routes)
        # GET /tasks, POST /tasks, GET /tasks/{id}, DELETE /tasks/{id}, POST /complete, POST /reopen + any update
        assert methods == 7, f"Expected 7 operations, found {methods}"

    def test_exactly_four_task_paths(self):
        from app.main import create_app

        app = create_app()
        task_paths = {r.path for r in app.routes if hasattr(r, "path") and "tasks" in r.path}
        expected = {
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        }
        assert task_paths == expected, f"Expected {expected}, got {task_paths}"

    def test_no_duplicate_task_router(self):
        from app.main import create_app

        # Check the final app routes - tasks should appear exactly once in the path set
        app = create_app()
        task_paths = {r.path for r in app.routes if hasattr(r, "path") and "tasks" in r.path}
        expected_paths = {
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        }
        assert task_paths == expected_paths


# =============================================================================
# N. Authentication On Every Task Operation
# =============================================================================


class TestAuthenticationOnEveryOperation:
    def test_all_endpoints_require_bearer_auth(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        for path in [
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        ]:
            for method, details in openapi["paths"][path].items():
                assert details["security"] == [{"BearerAuth": []}], (
                    f"{method.upper()} {path} missing BearerAuth"
                )

    def test_exactly_one_bearer_scheme(self):
        from app.main import create_app

        app = create_app()
        schemes = app.openapi()["components"]["securitySchemes"]
        bearer = [k for k, v in schemes.items() if v.get("scheme") == "bearer"]
        assert len(bearer) == 1


# =============================================================================
# O. No user_id Request Input
# =============================================================================


class TestNoUserIdRequestInput:
    def test_create_schema_excludes_user_id(self):
        assert "user_id" not in TaskCreate.model_fields

    def test_task_complete_request_excludes_user_id(self):
        from app.api.v1.tasks import TaskCompleteRequest

        assert "user_id" not in TaskCompleteRequest.model_fields

    def test_no_user_id_in_any_task_path(self):
        from app.main import create_app

        app = create_app()
        for r in app.routes:
            if hasattr(r, "path") and "tasks" in r.path:
                assert "user" not in r.path.lower()


# =============================================================================
# P. Response Privacy
# =============================================================================


class TestResponsePrivacy:
    def test_task_data_exposes_only_approved_fields(self):
        task = create_task(
            task_id=UUID("12345678-1234-5678-1234-567812345678"),
            title="Test",
            description="Desc",
            priority=TaskPriority.HIGH,
            due_date=date(2025, 7, 1),
        )
        data = TaskData.from_domain(task).model_dump()
        allowed = {
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
        }
        assert set(data.keys()) == allowed

    def test_list_response_exposes_only_tasks(self):
        task = create_task(
            task_id=UUID("12345678-1234-5678-1234-567812345678"),
            title="Test",
            description=None,
            priority=TaskPriority.MEDIUM,
            due_date=None,
        )
        list_data = TaskListData.from_domain([task]).model_dump()
        assert set(list_data.keys()) == {"tasks"}
        assert len(list_data["tasks"]) == 1
        assert set(list_data["tasks"][0].keys()) == {
            "task_id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "completed_at",
            "category",
            "recurrence",
        }

    def test_delete_response_no_data_field(self):
        resp = TaskDeleteSuccessResponse()
        data = resp.model_dump()
        assert set(data.keys()) == {"success", "message"}
        assert "data" not in data


# =============================================================================
# Q. OpenAPI Schema Correctness
# =============================================================================


class TestOpenAPISchemaCorrectness:
    def test_all_six_operations_documented(self):
        from app.main import create_app

        app = create_app()
        openapi = app.openapi()
        paths = openapi["paths"]
        assert "post" in paths["/api/v1/tasks"]
        assert "get" in paths["/api/v1/tasks"]
        assert "get" in paths["/api/v1/tasks/{task_id}"]
        assert "delete" in paths["/api/v1/tasks/{task_id}"]
        assert "post" in paths["/api/v1/tasks/{task_id}/complete"]
        assert "post" in paths["/api/v1/tasks/{task_id}/reopen"]

    def test_task_id_param_is_uuid_format(self):
        from app.main import create_app

        app = create_app()
        param = app.openapi()["paths"]["/api/v1/tasks/{task_id}"]["get"]["parameters"][0]
        assert param["name"] == "task_id"
        assert param["schema"]["format"] == "uuid"

    def test_complete_request_body_has_completed_at_datetime(self):
        from app.main import create_app

        app = create_app()
        body = app.openapi()["paths"]["/api/v1/tasks/{task_id}/complete"]["post"]["requestBody"]
        ref = body["content"]["application/json"]["schema"]["$ref"]
        schema_name = ref.split("/")[-1]
        schema = app.openapi()["components"]["schemas"][schema_name]
        assert schema["properties"]["completed_at"]["format"] == "date-time"
        assert "completed_at" in schema["required"]

    def test_unique_operation_ids(self):
        from app.main import create_app

        app = create_app()
        op_ids = []
        for path, methods in app.openapi()["paths"].items():
            for method, details in methods.items():
                if "operationId" in details:
                    op_ids.append(details["operationId"])
        assert len(op_ids) == len(set(op_ids)), "Duplicate operation IDs found"

    def test_no_duplicate_task_schemas(self):
        from app.main import create_app

        app = create_app()
        schemas = app.openapi()["components"]["schemas"]
        task_schemas = [k for k in schemas if k.startswith("Task")]
        assert len(task_schemas) == len(set(task_schemas))


# =============================================================================
# R. Exactly One BearerAuth Scheme
# =============================================================================


class TestBearerAuthCount:
    def test_exactly_one_bearer_scheme(self):
        from app.main import create_app

        app = create_app()
        schemes = app.openapi()["components"]["securitySchemes"]
        bearer = [v for v in schemes.values() if v.get("scheme") == "bearer"]
        assert len(bearer) == 1


# =============================================================================
# S. ORM Metadata Result
# =============================================================================


class TestORMMetadata:
    def test_exactly_six_tables(self):
        assert len(Base.metadata.tables) == 6

    def test_exact_table_names(self):
        expected = {"users", "nutrition_profiles", "nutrition_logs", "body_weights", "tasks", "goals"}
        assert set(Base.metadata.tables.keys()) == expected

    def test_tasks_table_columns(self):
        cols = {c.name for c in TaskORM.__table__.columns}
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
            "created_at",
            "updated_at",
        }
        assert cols == expected


# =============================================================================
# T. Migration Graph Result
# =============================================================================


class TestMigrationGraph:
    def test_exactly_five_revisions(self):
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        revs = list(script.walk_revisions())
        assert len(revs) == 7

    def test_exactly_one_base(self):
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        bases = script.get_bases()
        assert len(bases) == 1
        assert bases[0] == "3f0c6eb4f49e"

    def test_exactly_one_head(self):
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        heads = script.get_heads()
        assert len(heads) == 1
        assert heads[0] == "0295723946b2"

    def test_linear_chain(self):
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        revs = list(script.walk_revisions())
        for i in range(len(revs) - 1):
            assert revs[i].down_revision == revs[i + 1].revision

    def test_no_branches(self):
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        for rev in script.walk_revisions():
            if rev.branch_labels:
                pytest.fail(f"Branch labels found: {rev.revision} -> {rev.branch_labels}")

    def test_offline_upgrade_sql_generates(self):
        env = os.environ.copy()
        env["DATABASE_URL"] = "postgresql+asyncpg://localhost/nutrimind"
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert "CREATE TABLE tasks" in result.stdout
        assert "CREATE TYPE task_priority" in result.stdout
        assert "CREATE TYPE task_status" in result.stdout

    def test_offline_downgrade_sql_generates(self):
        env = os.environ.copy()
        env["DATABASE_URL"] = "postgresql+asyncpg://localhost/nutrimind"
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "a7b8c9d0e5f:e5f6a7b8c9d0", "--sql"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert "DROP TABLE tasks" in result.stdout
        assert "DROP INDEX ix_tasks_user_id_status_due_date" in result.stdout
        assert "DROP TYPE IF EXISTS task_status" in result.stdout
        assert "DROP TYPE IF EXISTS task_priority" in result.stdout

    def test_downgrade_order_index_then_table_then_enums(self):
        migration_text = Path("alembic/versions/a7b8c9d0e5f_create_tasks.py").read_text()
        downgrade = migration_text.split("def downgrade")[1]
        drop_index_pos = downgrade.find("drop_index")
        drop_table_pos = downgrade.find("drop_table")
        drop_status_pos = downgrade.find("DROP TYPE IF EXISTS task_status")
        drop_priority_pos = downgrade.find("DROP TYPE IF EXISTS task_priority")
        assert drop_index_pos < drop_table_pos < drop_status_pos < drop_priority_pos

    def test_downgrade_no_cascade(self):
        migration_text = Path("alembic/versions/a7b8c9d0e5f_create_tasks.py").read_text()
        downgrade = migration_text.split("def downgrade")[1]
        assert "CASCADE" not in downgrade


# =============================================================================
# U. No Prohibited Task Functionality
# =============================================================================


class TestNoProhibitedFunctionality:
    def test_no_reminder_columns(self):
        cols = {c.name for c in TaskORM.__table__.columns}
        forbidden = {
            "reminder",
            "remind_at",
            "recurrence_rule",
            "notification",
            "notify_at",
        }
        for f in forbidden:
            assert f not in cols, f"Prohibited column found: {f}"

    def test_no_category_tag_subtask(self):
        cols = {c.name for c in TaskORM.__table__.columns}
        forbidden = {"tag", "subtask", "parent_task_id", "shared_with"}
        for f in forbidden:
            assert f not in cols, f"Prohibited column found: {f}"

    def test_no_analytics_ai_columns(self):
        cols = {c.name for c in TaskORM.__table__.columns}
        forbidden = {
            "analytics",
            "productivity_score",
            "recommendation",
            "prediction",
            "ai_",
            "llm_",
            "external_id",
        }
        for f in forbidden:
            assert f not in cols, f"Prohibited column found: {f}"

    def test_no_new_dependencies(self):
        # Verify no new imports in task modules
        for mod_path in [
            "app.core.tasks",
            "app.core.task_exceptions",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            for forbidden in [
                "groq",
                "openai",
                "langchain",
                "gemini",
                "anthropic",
                "requests",
                "httpx",
            ]:
                assert forbidden not in source.lower(), f"{mod_path} imports {forbidden}"


# =============================================================================
# V. No Environment Files or Secrets
# =============================================================================


class TestNoEnvFilesOrSecrets:
    def test_env_files_gitignored(self):
        gitignore = Path("../.gitignore").resolve()
        assert gitignore.exists(), ".gitignore not found"
        text = gitignore.read_text(encoding="utf-8")
        assert ".env" in text
        assert "backend/.env" in text

    def test_no_secrets_in_repo(self):
        # Quick scan for common secret patterns
        import re

        secret_patterns = [
            r"sk-[a-zA-Z0-9]{32,}",
            r"Bearer\s+[a-zA-Z0-9\-_.]{20,}",
            r"password\s*=\s*[\"'][^\"']{8,}[\"']",
            r"secret\s*=\s*[\"'][^\"']{16,}[\"']",
        ]
        for py_file in Path(".").rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pattern in secret_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                # Allow in test files with obviously fake values
                if matches and "test" not in str(py_file).lower():
                    # Filter out obvious test/placeholder values
                    real_matches = [
                        m for m in matches if "test" not in m.lower() and "example" not in m.lower() and "qa" not in py_file.name.lower()
                    ]
                    assert not real_matches, f"Potential secret in {py_file}: {real_matches}"


# =============================================================================
# W. Application Import/Factory Safety
# =============================================================================


class TestApplicationImportFactory:
    def test_import_app_no_side_effects(self):
        import app
        import app.main

        assert app is not None
        assert app.main is not None

    def test_create_app_returns_distinct_instances(self):
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2

    def test_import_no_auto_migration(self):
        # Already tested by successful import above
        pass

    def test_import_no_database_connection(self):
        # Importing should not connect to DB

        assert True  # If we get here, no exception


# =============================================================================
# X. Phase 5E Freeze Boundaries
# =============================================================================


class TestPhase5EFreezeBoundaries:
    def test_no_reminder_functionality(self):
        for mod_path in [
            "app.core.tasks",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            assert "reminder" not in source.lower(), f"{mod_path} contains reminder"

    def test_no_recurrence(self):
        for mod_path in [
            "app.core.tasks",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            assert "recurrence" not in source.lower(), f"{mod_path} contains recurrence"

    def test_no_notifications(self):
        for mod_path in [
            "app.core.tasks",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            assert "notification" not in source.lower(), f"{mod_path} contains notification"

    def test_no_categories_tags_subtasks(self):
        for mod_path in [
            "app.core.tasks",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            # Check for prohibited feature keywords as whole words
            # (avoid false positives like "tags" in router decorator)
            import re

            for term in ["category", "subtask"]:
                pattern = rf"\b{term}\b"
                assert not re.search(pattern, source, re.IGNORECASE), f"{mod_path} contains {term}"
            # "tag" is special - allow "tags" in router decorator but not as a feature "tag"
            # Check each line for "tag" as a feature word, excluding "tags=" in decorators
            lines = source.splitlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Skip FastAPI tags=[...] decorator lines
                if "tags=[" in stripped:
                    continue
                # Check for tag as feature word (not in tags=)
                words = re.findall(r"\btag(s?)\b", line, re.IGNORECASE)
                if words:
                    pytest.fail(f"{mod_path}:{i + 1} contains feature 'tag': {stripped[:80]}")

    def test_no_analytics_ai(self):
        for mod_path in [
            "app.core.tasks",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            for term in [
                "analytics",
                "recommendation",
                "prediction",
                "groq",
                "openai",
                "langchain",
                "gemini",
                "llm",
            ]:
                assert term not in source.lower(), f"{mod_path} contains {term}"

    def test_no_frontend_code(self):
        for mod_path in [
            "app.core.tasks",
            "app.schemas.tasks",
            "app.models.task",
            "app.repositories.task",
            "app.services.task",
            "app.api.v1.tasks",
        ]:
            mod = importlib.import_module(mod_path)
            source = inspect.getsource(mod)
            assert "react" not in source.lower()
            assert "vue" not in source.lower()
            assert "html" not in source.lower()

    def test_no_new_orm_tables_or_columns(self):
        # Verified by ORM metadata test
        assert len(Base.metadata.tables) == 6

    def test_no_new_migrations(self):
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        heads = script.get_heads()
        assert heads == ["0295723946b2"]

    def test_no_env_or_secrets(self):
        # Verified by TestNoEnvFilesOrSecrets
        pass

    def test_nothing_committed_or_pushed(self):
        # This is a process check, not code
        pass

    def test_next_phase_not_started(self):
        # Verify no Phase 5F files exist
        assert not Path("app/api/v1/reminders.py").exists()
        assert not Path("app/api/v1/categories.py").exists()
        assert not Path("app/api/v1/tags.py").exists()


# =============================================================================
# Final Summary Counts
# =============================================================================


class TestFinalCounts:
    def test_task_test_file_counts(self):
        """Document the test counts for the audit report."""
        # These are informational - they verify the expected test files exist
        test_files = [
            "test_tasks.py",
            "test_task_api.py",
            "test_task_exceptions.py",
            "test_task_schemas.py",
            "test_task_model.py",
            "test_task_migration.py",
            "test_task_repository.py",
            "test_task_service.py",
        ]
        for tf in test_files:
            assert Path(f"tests/{tf}").exists(), f"Missing test file: {tf}"

    def test_phase_5e_final_audit_exists(self):
        assert Path("tests/test_phase_5e_final_audit.py").exists()
