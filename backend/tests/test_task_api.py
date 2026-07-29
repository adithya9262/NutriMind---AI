from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_settings as deps_get_settings
from app.core.config import Settings
from app.core.tasks import Task, TaskPriority, TaskStatus, order_tasks
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.task import Task as TaskORM
from app.models.user import User

VALID_COMPLETED_AT = "2026-07-12T10:00:00Z"
NOW = datetime.now(UTC)
TASK_TITLE = "Buy groceries"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_user(is_active: bool = True) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
    user.is_active = is_active
    return user


def _make_task_orm(
    *,
    user_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    title: str = TASK_TITLE,
    description: str | None = "a description",
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.PENDING,
    due_date: date | None = date(2026, 7, 12),
    completed_at: datetime | None = None,
) -> MagicMock:
    orm = MagicMock(spec=TaskORM)
    orm.id = uuid.uuid4()
    orm.user_id = user_id or uuid.uuid4()
    orm.task_id = task_id or uuid.uuid4()
    orm.title = title
    orm.description = description
    orm.priority = priority
    orm.status = status
    orm.due_date = due_date
    orm.completed_at = completed_at or (NOW if status is TaskStatus.COMPLETED else None)
    return orm


def _make_result(*, one_or_none=None, all_value=None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = one_or_none
    result.scalars.return_value.first.return_value = one_or_none
    result.scalars.return_value.all.return_value = all_value if all_value is not None else []
    return result


def _setup_create_session(mock_session: AsyncMock, user: MagicMock) -> None:
    
    mock_session.execute = AsyncMock(return_value=_make_result(one_or_none=user))
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()


def _setup_two_execute_session(
    mock_session: AsyncMock,
    user: MagicMock,
    task_value,
    *,
    as_list: bool = False,
) -> None:
    auth_result = _make_result(one_or_none=user)
    task_result = (
        _make_result(all_value=task_value) if as_list else _make_result(one_or_none=task_value)
    )
    
    mock_session.execute = AsyncMock(side_effect=[auth_result, task_result])
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()


def _domain_from_orm(orm: MagicMock) -> Task:
    return Task(
        task_id=orm.task_id,
        title=orm.title,
        description=orm.description,
        priority=orm.priority,
        status=orm.status,
        due_date=orm.due_date,
        completed_at=orm.completed_at,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        APP_ENV="test",
        DEBUG=False,
        CORS_ORIGINS="http://test",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    return _make_session()


@pytest.fixture
def app(test_settings, mock_session):
    application = create_app(settings=test_settings)
    application.dependency_overrides[deps_get_settings] = lambda: test_settings

    async def override_get_db_session():
        try:
            yield mock_session
        finally:
            pass

    application.dependency_overrides[get_db_session] = override_get_db_session
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _auth_header(token: str | None) -> dict[str, str]:
    return {"Authorization": token} if token else {}


# ===========================================================================
# A. Router Registration
# ===========================================================================


class TestRouteRegistration:
    async def test_router_exists(self, app):
        paths = [r.path for r in app.routes if "tasks" in r.path]
        assert len(paths) > 0

    async def test_paths_registered(self, app):
        task_paths = {r.path for r in app.routes if "tasks" in r.path}
        assert task_paths == {
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        }

    async def test_post_path_exists(self, client):
        response = await client.post("/api/v1/tasks", json={"title": "x"})
        assert response.status_code != 404

    async def test_get_list_path_exists(self, client):
        response = await client.get("/api/v1/tasks")
        assert response.status_code != 404

    async def test_get_one_path_exists(self, client):
        response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}")
        assert response.status_code != 404

    async def test_complete_path_exists(self, client):
        response = await client.post(
            f"/api/v1/tasks/{uuid.uuid4()}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
        )
        assert response.status_code != 404

    async def test_reopen_path_exists(self, client):
        response = await client.post(f"/api/v1/tasks/{uuid.uuid4()}/reopen")
        assert response.status_code != 404

    async def test_delete_path_exists(self, client):
        response = await client.delete(f"/api/v1/tasks/{uuid.uuid4()}")
        assert response.status_code != 404

    async def test_no_extra_post_endpoint(self, app):
        post_paths = [
            r.path
            for r in app.routes
            if "tasks" in r.path and hasattr(r, "methods") and "POST" in r.methods
        ]
        assert len(post_paths) == 3

    async def test_no_user_id_path(self, app):
        paths = [r.path for r in app.routes if "users/" in r.path and "tasks" in r.path]
        assert len(paths) == 0

    async def test_no_put_endpoint(self, client):
        response = await client.put("/api/v1/tasks")
        assert response.status_code == 405

    async def test_no_patch_endpoint(self, client):
        response = await client.patch("/api/v1/tasks")
        assert response.status_code == 405

    async def test_registered_exactly_once(self, app):
        task_paths = {r.path for r in app.routes if "tasks" in r.path}
        assert task_paths == {
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        }


# ===========================================================================
# B. Static-route ordering and path-collision safety
# ===========================================================================


class TestRouteOrdering:
    async def test_no_put_on_tasks(self, client):
        response = await client.put("/api/v1/tasks")
        assert response.status_code == 405

    async def test_malformed_uuid_returns_422(self, client, test_settings, mock_session):
        _setup_create_session(mock_session, _make_user())
        token = create_access_token(user_id=_make_user().id, settings=test_settings)
        response = await client.get(
            "/api/v1/tasks/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_complete_subpath_not_captured_by_task_id(self, client):
        response = await client.post(
            "/api/v1/tasks/some-id/complete",
            json={"completed_at": VALID_COMPLETED_AT},
        )
        assert response.status_code != 404

    async def test_static_before_dynamic(self, app):
        task_paths = sorted(r.path for r in app.routes if "tasks" in r.path)
        assert task_paths[0] == "/api/v1/tasks"
        assert "/api/v1/tasks/{task_id}" in task_paths


# ===========================================================================
# C. OpenAPI
# ===========================================================================


class TestOpenAPI:
    def _openapi(self):
        return create_app().openapi()

    def test_task_paths_present(self):
        paths = self._openapi()["paths"]
        assert "/api/v1/tasks" in paths
        assert "/api/v1/tasks/{task_id}" in paths
        assert "/api/v1/tasks/{task_id}/complete" in paths
        assert "/api/v1/tasks/{task_id}/reopen" in paths

    def test_methods_and_operation_ids(self):
        paths = self._openapi()["paths"]
        assert "post" in paths["/api/v1/tasks"]
        assert "get" in paths["/api/v1/tasks"]
        assert "get" in paths["/api/v1/tasks/{task_id}"]
        assert "delete" in paths["/api/v1/tasks/{task_id}"]
        assert "post" in paths["/api/v1/tasks/{task_id}/complete"]
        assert "post" in paths["/api/v1/tasks/{task_id}/reopen"]

        op_ids = {
            paths["/api/v1/tasks"]["post"]["operationId"],
            paths["/api/v1/tasks"]["get"]["operationId"],
            paths["/api/v1/tasks/{task_id}"]["get"]["operationId"],
            paths["/api/v1/tasks/{task_id}"]["delete"]["operationId"],
            paths["/api/v1/tasks/{task_id}/complete"]["post"]["operationId"],
            paths["/api/v1/tasks/{task_id}/reopen"]["post"]["operationId"],
        }
        assert len(op_ids) == 6

    def test_bearer_required_on_all(self):
        paths = self._openapi()["paths"]
        for path in [
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/complete",
            "/api/v1/tasks/{task_id}/reopen",
        ]:
            for method in paths[path]:
                assert paths[path][method]["security"] == [{"BearerAuth": []}]

    def test_exactly_one_bearer_scheme(self):
        schemes = self._openapi()["components"]["securitySchemes"]
        bearer = [v for v in schemes.values() if v.get("scheme") == "bearer"]
        assert len(bearer) == 1

    def test_task_id_param_is_uuid(self):
        param = create_app().openapi()["paths"]["/api/v1/tasks/{task_id}"]["get"]["parameters"][0]
        assert param["name"] == "task_id"
        assert param["schema"]["format"] == "uuid"

    def test_complete_request_body_datetime(self):
        body = create_app().openapi()["paths"]["/api/v1/tasks/{task_id}/complete"]["post"][
            "requestBody"
        ]["content"]["application/json"]["schema"]
        ref = body["$ref"]
        assert ref.endswith("TaskCompleteRequest")
        schema = create_app().openapi()["components"]["schemas"]["TaskCompleteRequest"]
        assert schema["properties"]["completed_at"]["format"] == "date-time"
        assert "completed_at" in schema["required"]

    def test_response_schemas_reference_task_components(self):
        paths = create_app().openapi()["paths"]
        create_ref = paths["/api/v1/tasks"]["post"]["responses"]["201"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        list_ref = paths["/api/v1/tasks"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        assert create_ref.endswith("TaskSuccessResponse")
        assert list_ref.endswith("TaskListSuccessResponse")


# ===========================================================================
# D. Authentication
# ===========================================================================


ENDPOINTS = [
    ("POST", "/api/v1/tasks", {"title": "Task"}),
    ("GET", "/api/v1/tasks", None),
    ("GET", "/api/v1/tasks/{tid}", None),
    (
        "POST",
        "/api/v1/tasks/{tid}/complete",
        {"completed_at": VALID_COMPLETED_AT},
    ),
    ("POST", "/api/v1/tasks/{tid}/reopen", None),
    ("DELETE", "/api/v1/tasks/{tid}", None),
]


def _build_url(method_url: str) -> str:
    tid = str(uuid.uuid4())
    return method_url.replace("{tid}", tid)


async def _call_endpoint(client, method, url, header, json_body):
    headers = _auth_header(header)
    kwargs = {}
    if json_body is not None:
        kwargs["json"] = json_body
    return await client.request(method, url, headers=headers, **kwargs)


class TestAuthMissingHeader:
    async def test_all_endpoints_401(self, client):
        for method, url, body in ENDPOINTS:
            response = await _call_endpoint(client, method, _build_url(url), None, body)
            assert response.status_code == 401, (method, url, response.status_code)

    async def test_post_safe_envelope(self, client):
        response = await client.post("/api/v1/tasks", json={"title": "x"}, headers={})
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_post_www_authenticate(self, client):
        response = await client.post("/api/v1/tasks", json={"title": "x"}, headers={})
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_post_no_detail_field(self, client):
        response = await client.post("/api/v1/tasks", json={"title": "x"}, headers={})
        assert '"detail"' not in response.text


class TestAuthMalformedToken:
    async def test_all_endpoints_401(self, client):
        for method, url, body in ENDPOINTS:
            response = await _call_endpoint(client, method, _build_url(url), "token123", body)
            assert response.status_code == 401, (method, url, response.status_code)

    async def test_post_code(self, client):
        response = await client.post(
            "/api/v1/tasks", json={"title": "x"}, headers={"Authorization": "token123"}
        )
        assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


class TestAuthInvalidToken:
    async def test_all_endpoints_401(self, client):
        for method, url, body in ENDPOINTS:
            response = await _call_endpoint(
                client, method, _build_url(url), "Bearer not-a-valid-token", body
            )
            assert response.status_code == 401, (method, url, response.status_code)

    async def test_post_code(self, client):
        response = await client.post(
            "/api/v1/tasks",
            json={"title": "x"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.json()["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=uuid.uuid4(), settings=settings, now=past)

    async def test_all_endpoints_401(self, client, test_settings):
        token = f"Bearer {self._make_expired_token(test_settings)}"
        for method, url, body in ENDPOINTS:
            response = await _call_endpoint(client, method, _build_url(url), token, body)
            assert response.status_code == 401, (method, url, response.status_code)

    async def test_post_code(self, client, test_settings):
        token = f"Bearer {self._make_expired_token(test_settings)}"
        response = await client.post(
            "/api/v1/tasks", json={"title": "x"}, headers={"Authorization": token}
        )
        assert response.json()["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    async def test_all_endpoints_401(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_result(one_or_none=None))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        for method, url, body in ENDPOINTS:
            response = await _call_endpoint(
                client, method, _build_url(url), f"Bearer {token}", body
            )
            assert response.status_code == 401, (method, url, response.status_code)


class TestAuthInactiveUser:
    async def test_all_endpoints_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        mock_session.execute = AsyncMock(return_value=_make_result(one_or_none=user))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        for method, url, body in ENDPOINTS:
            response = await _call_endpoint(
                client, method, _build_url(url), f"Bearer {token}", body
            )
            assert response.status_code == 403, (method, url, response.status_code)

    async def test_post_code(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        mock_session.execute = AsyncMock(return_value=_make_result(one_or_none=user))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": "x"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "INACTIVE_ACCOUNT"


# ===========================================================================
# E. POST Success
# ===========================================================================


class TestPostSuccess:
    async def test_returns_201(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    async def test_success_is_true(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["message"] == "Task created successfully."

    async def test_task_data_returned(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE, "description": "desc", "priority": "high"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "data" in data
        task = data["data"]
        assert task["title"] == TASK_TITLE
        assert task["description"] == "desc"
        assert task["priority"] == "high"
        assert task["status"] == "pending"
        assert "task_id" in task

    async def test_commits_exactly_once(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_no_user_id_request_param(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        body = {"title": TASK_TITLE, "user_id": str(uuid.uuid4())}
        response = await client.post(
            "/api/v1/tasks",
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# F. POST Validation
# ===========================================================================


class TestPostValidation:
    async def test_empty_title_422(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_extra_field_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE, "extra": "x"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_user_id_injection_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE, "user_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_invalid_priority_422(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE, "priority": "urgent"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_validation_error_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"


# ===========================================================================
# G. Duplicate Task ID
# ===========================================================================


class TestPostDuplicate:
    async def test_returns_409(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_error_code(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "TASK_ID_ALREADY_EXISTS"

    async def test_rollback_called(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_awaited_once()

    async def test_no_commit(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_safe_message(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "already exists" in text
        assert "constraint" not in text
        assert "integrity" not in text


# ===========================================================================
# H. GET list success
# ===========================================================================


class TestGetListSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, [orm], as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    async def test_success_and_message(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, [orm], as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Tasks retrieved successfully."

    async def test_task_data_returned(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, [orm], as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert len(data["data"]["tasks"]) == 1
        assert data["data"]["tasks"][0]["task_id"] == str(orm.task_id)

    async def test_no_commit_flush_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, [orm], as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        mock_session.commit.assert_not_called()
        mock_session.flush.assert_not_called()
        mock_session.refresh.assert_not_called()

    async def test_uses_current_user_only(self, client, test_settings, mock_session):
        from app.services.task import TaskService

        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, [orm], as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(TaskService, "list_tasks", AsyncMock(return_value=()))
            await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
            args = TaskService.list_tasks.await_args
            assert args.kwargs["user_id"] == user.id


# ===========================================================================
# I. Empty task list
# ===========================================================================


class TestGetEmptyList:
    async def test_empty_list(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, [], as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["data"]["tasks"] == []


# ===========================================================================
# J. Deterministic ordering preservation
# ===========================================================================


class TestGetOrdering:
    async def test_ordering_preserved(self, client, test_settings, mock_session):
        user = _make_user()
        completed_low = _make_task_orm(
            user_id=user.id,
            title="completed",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.LOW,
            due_date=date(2026, 1, 1),
            completed_at=NOW,
        )
        pending_high = _make_task_orm(
            user_id=user.id,
            title="high",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            due_date=None,
        )
        pending_medium = _make_task_orm(
            user_id=user.id,
            title="medium",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            due_date=date(2026, 5, 1),
        )
        shuffled = [completed_low, pending_medium, pending_high]
        _setup_two_execute_session(mock_session, user, shuffled, as_list=True)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        returned_ids = [t["task_id"] for t in data["data"]["tasks"]]

        expected = order_tasks(tasks=[_domain_from_orm(o) for o in shuffled])
        expected_ids = [str(t.task_id) for t in expected]
        assert returned_ids == expected_ids
        # The frozen domain ordering is preserved exactly (pending before
        # completed; tasks with a due date before undated tasks; higher
        # priority before lower priority among same due-date class).
        assert data["data"]["tasks"][-1]["status"] == "completed"
        assert all(t["status"] == "pending" for t in data["data"]["tasks"][:-1])


# ===========================================================================
# K. GET-by-ID success
# ===========================================================================


class TestGetByIdSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{orm.task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_task_data_returned(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{orm.task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["data"]["task_id"] == str(orm.task_id)
        assert data["message"] == "Task retrieved successfully."

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            f"/api/v1/tasks/{orm.task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()
        mock_session.flush.assert_not_called()


# ===========================================================================
# L. Missing task
# ===========================================================================


class TestGetMissing:
    async def test_returns_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


# ===========================================================================
# M. Wrong-user isolation
# ===========================================================================


class TestWrongUserIsolation:
    async def test_get_by_id_wrong_user_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TASK_NOT_FOUND"

    async def test_route_uses_current_user_id(self, client, test_settings, mock_session):
        from app.services.task import TaskService

        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                TaskService,
                "get_task",
                AsyncMock(return_value=_domain_from_orm(orm)),
            )
            await client.get(
                f"/api/v1/tasks/{orm.task_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert TaskService.get_task.await_args.kwargs["user_id"] == user.id

    async def test_complete_wrong_user_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{uuid.uuid4()}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TASK_NOT_FOUND"

    async def test_reopen_wrong_user_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{uuid.uuid4()}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TASK_NOT_FOUND"

    async def test_delete_wrong_user_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


# ===========================================================================
# N. Complete success
# ===========================================================================


class TestCompleteSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_and_message(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Task completed successfully."

    async def test_commits_once(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()


# ===========================================================================
# O. Already-completed error
# ===========================================================================


class TestAlreadyCompleted:
    async def test_returns_409(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.COMPLETED, completed_at=NOW)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.COMPLETED, completed_at=NOW)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "TASK_ALREADY_COMPLETED"

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.COMPLETED, completed_at=NOW)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()


# ===========================================================================
# P. Caller-supplied completed_at preservation
# ===========================================================================


class TestCallerSuppliedCompletedAt:
    async def test_completed_at_preserved(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["status"] == "completed"
        assert data["data"]["completed_at"] == VALID_COMPLETED_AT


# ===========================================================================
# Q. No system-clock fallback
# ===========================================================================


class TestNoSystemClockFallback:
    async def test_completed_at_not_from_clock(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["completed_at"] == VALID_COMPLETED_AT

    def test_route_never_consults_system_clock(self):
        import inspect

        from app.api.v1 import tasks as tasks_module

        source = inspect.getsource(tasks_module)
        # The route must never fall back to the system clock for completed_at.
        assert "datetime.now" not in source
        assert "datetime.utcnow" not in source
        assert "utcnow" not in source
        assert ".now(" not in source


# ===========================================================================
# R. Reopen success
# ===========================================================================


class TestReopenSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.COMPLETED, completed_at=NOW)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_and_message(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.COMPLETED, completed_at=NOW)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Task reopened successfully."
        assert data["data"]["status"] == "pending"
        assert data["data"]["completed_at"] is None

    async def test_commits_once(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.COMPLETED, completed_at=NOW)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            f"/api/v1/tasks/{orm.task_id}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()


# ===========================================================================
# S. Reopen-pending error
# ===========================================================================


class TestReopenPending:
    async def test_returns_409(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "TASK_NOT_COMPLETED"

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            f"/api/v1/tasks/{orm.task_id}/reopen",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()


# ===========================================================================
# T. DELETE success
# ===========================================================================


class TestDeleteSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/tasks/{orm.task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_and_message(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/tasks/{orm.task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Task deleted successfully."
        assert "data" not in data

    async def test_commits_once(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/tasks/{orm.task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()


# ===========================================================================
# U. DELETE missing / wrong-user
# ===========================================================================


class TestDeleteMissing:
    async def test_missing_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TASK_NOT_FOUND"

    async def test_no_commit_on_missing(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()


# ===========================================================================
# V. Exact commit counts
# ===========================================================================


class TestCommitCounts:
    async def test_all_writes_commit_once(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id, status=TaskStatus.PENDING)
        token = create_access_token(user_id=user.id, settings=test_settings)
        headers = {"Authorization": f"Bearer {token}"}

        _setup_create_session(mock_session, user)
        await client.post("/api/v1/tasks", json={"title": TASK_TITLE}, headers=headers)
        mock_session.commit.assert_awaited_once()
        mock_session.commit.reset_mock()

        _setup_two_execute_session(mock_session, user, orm)
        response = await client.post(
            f"/api/v1/tasks/{orm.task_id}/complete",
            json={"completed_at": VALID_COMPLETED_AT},
            headers=headers,
        )
        print("RESPONSE:", response.text)
        mock_session.commit.assert_awaited_once()
        mock_session.commit.reset_mock()

        _setup_two_execute_session(mock_session, user, orm)
        await client.post(f"/api/v1/tasks/{orm.task_id}/reopen", headers=headers)
        mock_session.commit.assert_awaited_once()
        mock_session.commit.reset_mock()

        _setup_two_execute_session(mock_session, user, orm)
        await client.delete(f"/api/v1/tasks/{orm.task_id}", headers=headers)
        mock_session.commit.assert_awaited_once()


# ===========================================================================
# X. Rollback behavior on expected write failures
# ===========================================================================


class TestRollbackBehavior:
    async def test_commit_failure_rolls_back(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_awaited_once()
        mock_session.commit.assert_not_called()

    async def test_commit_exception_returns_503(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        mock_session.commit = AsyncMock(side_effect=Exception("db down"))
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503
        mock_session.rollback.assert_awaited()


# ===========================================================================
# Y. Unexpected-error handling
# ===========================================================================


class TestUnexpectedError:
    async def test_unexpected_returns_500(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_global_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_no_raw_exception_text(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "RuntimeError" not in response.text
        assert "db down" not in response.text


# ===========================================================================
# Z. Request-ID preservation
# ===========================================================================


class TestRequestId:
    async def test_present_on_success(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        assert "X-Request-ID" in response.headers

    async def test_present_in_error_body(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]


# ===========================================================================
# AA. Safe error messages
# ===========================================================================


class TestSafeMessages:
    async def test_no_sql_in_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_two_execute_session(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            f"/api/v1/tasks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "select" not in text
        assert "insert" not in text
        assert "constraint" not in text
        assert "traceback" not in text

    async def test_no_sql_in_duplicate(self, client, test_settings, mock_session):
        from app.core.task_exceptions import DuplicateTaskIdError

        user = _make_user()
        _setup_create_session(mock_session, user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateTaskIdError())
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "constraint" not in text
        assert "integrity" not in text


# ===========================================================================
# AB. Response privacy
# ===========================================================================


class TestResponsePrivacy:
    async def test_no_user_id_password_email(self, client, test_settings, mock_session):
        user = _make_user()
        orm = _make_task_orm(user_id=user.id)
        _setup_two_execute_session(mock_session, user, orm)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
        text = response.text.lower()
        assert "user_id" not in text
        assert "password" not in text
        assert user.email not in response.text
        assert "created_at" not in text
        assert "updated_at" not in text

    async def test_no_internal_id_in_create(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "id" not in data["data"]
        assert "user_id" not in data["data"]


# ===========================================================================
# AC. No user_id request parameter
# ===========================================================================


class TestNoUserIdRequestParameter:
    async def test_post_user_id_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_create_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/tasks",
            json={"title": TASK_TITLE, "user_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_source_has_no_user_id_param(self):
        import inspect

        from app.api.v1 import tasks as tasks_module

        for name, func in inspect.getmembers(tasks_module, inspect.iscoroutinefunction):
            if name.startswith(("create", "list", "get", "complete", "reopen", "delete")):
                sig = inspect.signature(func)
                for pname in sig.parameters:
                    assert pname != "user_id", f"{name} exposes user_id parameter"


# ===========================================================================
# AD. Repository / service reuse
# ===========================================================================


class TestRepositoryServiceReuse:
    def test_source_uses_repository_and_service(self):
        import inspect

        from app.api.v1 import tasks as tasks_module

        source = inspect.getsource(tasks_module)
        assert "TaskRepository(" in source
        assert "TaskService(" in source
        # No raw SQLAlchemy queries for tasks in the API layer.
        assert "select(TaskORM" not in source
        assert "session.execute(" not in source


# ===========================================================================
# AE. No route-level logic duplication
# ===========================================================================


class TestNoLogicDuplication:
    def test_no_ordering_in_route(self):
        import inspect

        from app.api.v1 import tasks as tasks_module

        source = inspect.getsource(tasks_module)
        assert "order_tasks" not in source

    def test_domain_complete_reopen_only_via_service(self):
        import inspect

        from app.api.v1 import tasks as tasks_module

        source = inspect.getsource(tasks_module)
        assert "service.complete_task" in source
        assert "service.reopen_task" in source
        assert "\ncomplete_task(" not in source
        assert "\nreopen_task(" not in source


# ===========================================================================
# AG. Phase-boundary enforcement
# ===========================================================================


class TestPhaseBoundary:
    def test_task_router_file_exists(self):
        import os

        assert os.path.exists("app/api/v1/tasks.py")

    def test_frozen_repository_exists(self):
        import os

        assert os.path.exists("app/repositories/task.py")

    def test_frozen_service_exists(self):
        import os

        assert os.path.exists("app/services/task.py")

    def test_no_orm_or_migration_changes(self):
        from app.db.base import Base

        assert set(Base.metadata.tables.keys()) == {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }

    def test_task_routes_in_openapi(self):
        from app.main import create_app

        paths = create_app().openapi().get("paths", {})
        task_paths = [p for p in paths if "task" in p.lower()]
        assert "/api/v1/tasks" in task_paths
        assert "/api/v1/tasks/{task_id}" in task_paths
        assert "/api/v1/tasks/{task_id}/complete" in task_paths
        assert "/api/v1/tasks/{task_id}/reopen" in task_paths
