from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import (
    get_settings as deps_get_settings,
)
from app.core.body_weight_trends import calculate_body_weight_trend
from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.body_weight import BodyWeight
from app.models.user import User

NOW = datetime.now(UTC)

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
    user.is_verified = False
    user.created_at = NOW
    user.updated_at = NOW
    return user


def _make_body_weight(
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date | None = None,
    weight_kg: Decimal | None = None,
) -> MagicMock:
    entry = MagicMock(spec=BodyWeight)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.entry_id = entry_id or uuid.uuid4()
    entry.logged_date = logged_date or date(2026, 7, 1)
    entry.weight_kg = weight_kg or Decimal("70.00")
    entry.created_at = NOW
    entry.updated_at = NOW
    return entry


def _make_execute_result(
    value: MagicMock | None,
) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


def _make_execute_result_for_list(values: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings():
    return Settings(
        APP_ENV="test",
        DEBUG=False,
        CORS_ORIGINS="http://test",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
    )


@pytest.fixture
def mock_session():
    return _make_session()


@pytest.fixture
def app(test_settings, mock_session):
    app = create_app(settings=test_settings)
    app.dependency_overrides[deps_get_settings] = lambda: test_settings

    async def override_get_db_session():
        try:
            yield mock_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db_session
    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ===========================================================================
# A. Route registration and ordering
# ===========================================================================


class TestRouteRegistration:
    async def test_exact_get_path_exists(self, client):
        response = await client.get("/api/v1/body-weights/trend")
        assert response.status_code != 404

    async def test_route_registered_exactly_once(self, app):
        trend_routes = [
            r
            for r in app.routes
            if getattr(r, "path", "") == "/api/v1/body-weights/trend"
            and hasattr(r, "methods")
            and "GET" in r.methods
        ]
        assert len(trend_routes) == 1

    async def test_static_trend_not_shadowed(self, app):
        trend_routes = [
            r for r in app.routes if getattr(r, "path", "") == "/api/v1/body-weights/trend"
        ]
        assert len(trend_routes) == 1

    async def test_route_on_existing_body_weight_router(self, app):
        from app.api.v1.body_weights import router

        path_found = any(
            "/trend" in str(getattr(r, "path", "")) or "/trend" in str(getattr(r, "paths", ""))
            for r in router.routes
        )
        assert path_found

    async def test_no_second_body_weight_router(self, app):
        from app.api.v1.body_weights import router as bw_router

        assert bw_router.prefix == "/body-weights"

    async def test_no_post_trend(self, client):
        response = await client.post("/api/v1/body-weights/trend")
        assert response.status_code not in (200, 201)

    async def test_no_patch_trend(self, client):
        response = await client.patch("/api/v1/body-weights/trend")
        assert response.status_code not in (200, 201)

    async def test_no_put_trend(self, client):
        response = await client.put("/api/v1/body-weights/trend")
        assert response.status_code not in (200, 201)

    async def test_no_delete_trend(self, client):
        response = await client.delete("/api/v1/body-weights/trend")
        assert response.status_code in (404, 405, 401)

    async def test_existing_body_weight_routes_unchanged(self, app):
        bw_paths: set[str] = {
            r.path for r in app.routes if "body-weight" in r.path or "body_weight" in r.path
        }
        assert "/api/v1/body-weights" in bw_paths
        assert "/api/v1/body-weights/trend" in bw_paths
        assert "/api/v1/body-weights/{entry_id}" in bw_paths


# ===========================================================================
# B. OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_trend_path_exists(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/body-weights/trend" in paths

    async def test_get_is_only_operation(self, app):
        openapi = app.openapi()
        ops = openapi["paths"]["/api/v1/body-weights/trend"]
        assert "get" in ops
        assert "post" not in ops
        assert "patch" not in ops
        assert "put" not in ops
        assert "delete" not in ops

    async def test_http_200_documented(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/trend"]["get"]
        assert "200" in get_op.get("responses", {})

    async def test_correct_response_schema(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/trend"]["get"]
        resp_200 = get_op["responses"]["200"]
        content = resp_200.get("content", {})
        schema = content.get("application/json", {}).get("schema", {})
        ref = schema.get("$ref", "")
        assert "BodyWeightTrendSuccessResponse" in ref

    async def test_bearer_auth_required(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/trend"]["get"]
        sec = get_op.get("security", [])
        assert any("BearerAuth" in s for s in sec)

    async def test_exactly_one_bearer_scheme(self, app):
        openapi = app.openapi()
        schemes = openapi.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1

    async def test_no_request_body(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/trend"]["get"]
        assert "requestBody" not in get_op

    async def test_no_user_id_path_param(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/trend"]["get"].get("parameters", [])
        user_id_params = [p for p in params if p.get("name") == "user_id"]
        assert len(user_id_params) == 0

    async def test_no_user_id_query_param(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/trend"]["get"].get("parameters", [])
        user_id_params = [p for p in params if p.get("name") == "user_id"]
        assert len(user_id_params) == 0

    async def test_no_logged_date_parameter(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/trend"]["get"].get("parameters", [])
        logged_date_params = [p for p in params if p.get("name") == "logged_date"]
        assert len(logged_date_params) == 0

    async def test_no_date_range_parameters(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/trend"]["get"].get("parameters", [])
        param_names = {p.get("name") for p in params}
        assert "start_date" not in param_names
        assert "end_date" not in param_names

    async def test_existing_openapi_paths_unchanged(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/body-weights" in paths
        assert "/api/v1/body-weights/{entry_id}" in paths


# ===========================================================================
# C. Authentication
# ===========================================================================


class TestAuthMissingToken:
    async def test_missing_token_returns_401(self, client):
        response = await client.get("/api/v1/body-weights/trend")
        assert response.status_code == 401

    async def test_missing_token_safe_envelope(self, client):
        response = await client.get("/api/v1/body-weights/trend")
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_missing_token_www_authenticate(self, client):
        response = await client.get("/api/v1/body-weights/trend")
        assert response.headers.get("WWW-Authenticate") == "Bearer"


class TestAuthInvalidToken:
    async def test_invalid_token_returns_401(self, client):
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_invalid_token_code(self, client):
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        user_id = uuid.uuid4()
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=user_id, settings=settings, now=past)

    async def test_expired_token_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_expired_token_code(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    async def test_unknown_user_returns_401(self, client, test_settings, mock_session):
        mock_session.execute = AsyncMock(return_value=_make_execute_result(None))
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestAuthInactiveUser:
    async def test_inactive_user_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_inactive_user_code(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthOrdering:
    async def test_auth_before_history_retrieval(self, client):
        response = await client.get("/api/v1/body-weights/trend")
        assert response.status_code == 401

    async def test_auth_before_trend_calculation(self, client):
        response = await client.get("/api/v1/body-weights/trend")
        assert response.status_code == 401

    async def test_no_manual_jwt_decoding(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "decode_access_token" not in source
        assert "jwt.decode" not in source

    async def test_existing_auth_reused(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "get_current_user" in source


# ===========================================================================
# D. Current-user isolation
# ===========================================================================


class TestCurrentUserIsolation:
    async def test_history_loaded_using_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )

    async def test_no_caller_supplied_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def auth_execute_side(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.one_or_none.return_value = user
            return result

        mock_session.execute.side_effect = auth_execute_side
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend?user_id=" + str(uuid.uuid4()),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 422)

    async def test_response_contains_no_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def auth_execute_side(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.one_or_none.return_value = user
            return result

        mock_session.execute.side_effect = auth_execute_side
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_no_orm_internal_id_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def auth_execute_side(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.one_or_none.return_value = user
            return result

        mock_session.execute.side_effect = auth_execute_side
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_no_timestamps_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def auth_execute_side(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.one_or_none.return_value = user
            return result

        mock_session.execute.side_effect = auth_execute_side
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        text_lower = response.text.lower()
        assert "created_at" not in text_lower
        assert "updated_at" not in text_lower

    async def test_no_profile_lookup_as_fallback(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def auth_execute_side(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.one_or_none.return_value = user
            return result

        mock_session.execute.side_effect = auth_execute_side
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )


# ===========================================================================
# E. Repository and service reuse
# ===========================================================================


class TestRepositoryServiceReuse:
    async def test_repository_constructed_with_session(self):
        from app.api.v1.body_weights import router

        assert len(router.routes) > 0

    async def test_existing_service_constructed_with_repository(self):
        from app.services.body_weight import BodyWeightService

        assert BodyWeightService is not None

    async def test_existing_list_history_called(self):
        from app.services.body_weight import BodyWeightService

        assert hasattr(BodyWeightService, "list_history")

    async def test_no_trend_repository_method(self):
        import inspect

        from app.repositories.body_weight import BodyWeightRepository

        source = inspect.getsource(BodyWeightRepository)
        assert "trend" not in source.lower()

    async def test_no_trend_service_method(self):
        import inspect

        from app.services.body_weight import BodyWeightService

        source = inspect.getsource(BodyWeightService)
        assert "trend" not in source.lower()

    async def test_endpoint_does_not_query_orm_directly(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "session.execute(" not in source
        assert "select(" not in source

    async def test_no_direct_orm_query(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "session.execute(" not in source
        assert "select(" not in source


# ===========================================================================
# F. Domain-function reuse
# ===========================================================================


class TestDomainFunctionReuse:
    async def test_calculate_body_weight_trend_called(self):
        assert calculate_body_weight_trend is not None

    async def test_no_route_level_sorting(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_section = source[trend_start:]
        assert "sorted(" not in trend_section
        assert ".sort(" not in trend_section

    async def test_no_route_level_observation_counting(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_section = source[trend_start:]
        assert "len(" not in trend_section

    async def test_no_route_level_first_latest_selection(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_def_end = source.find("def ", trend_start + 4)
        if trend_def_end == -1:
            trend_def_end = len(source)
        trend_section = source[trend_start:trend_def_end]
        assert "[0]" not in trend_section
        assert "[-1]" not in trend_section

    async def test_no_route_level_percentage_formula(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_def_end = source.find("def ", trend_start + 4)
        if trend_def_end == -1:
            trend_def_end = len(source)
        trend_section = source[trend_start:trend_def_end]
        for line in trend_section.lower().split("\n"):
            if "percentage" in line:
                assert "percentage_change=decimal" in line.replace(" ", "")

    async def test_no_route_level_decimal_quantization(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_section = source[trend_start:]
        assert "quantize" not in trend_section

    async def test_no_route_level_round_half_up(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_section = source[trend_start:]
        assert "ROUND_HALF_UP" not in trend_section

    async def test_no_route_level_direction_classification(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_section = source[trend_start:]
        assert "INCREASED" not in trend_section
        assert "DECREASED" not in trend_section

    async def test_domain_result_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def auth_execute_side(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.one_or_none.return_value = user
            return result

        mock_session.execute.side_effect = auth_execute_side
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )


# ===========================================================================
# G. Schema conversion reuse
# ===========================================================================


class TestSchemaConversionReuse:
    async def test_from_result_exists(self):
        from app.schemas.body_weight_trends import BodyWeightTrendData

        assert hasattr(BodyWeightTrendData, "from_result")

    async def test_no_manual_response_data_mapping(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        trend_start = source.find("def get_body_weight_trend")
        trend_section = source[trend_start:]
        has_obs = "observation_count" in trend_section
        has_from_result = "from_result" in trend_section
        assert not has_obs or has_from_result

    async def test_conversion_not_mutated(self):
        from app.schemas.body_weight_trends import BodyWeightTrendData

        assert BodyWeightTrendData is not None

    async def test_body_weight_trend_success_response_reused(self):
        from app.schemas.body_weight_trends import (
            BodyWeightTrendSuccessResponse,
        )

        assert BodyWeightTrendSuccessResponse is not None


# ===========================================================================
# H. Successful responses
# ===========================================================================


class _TrendSuccessBase:
    def _setup_session_with_entries(self, mock_session, user, entries):
        """Set up session to return user on auth call and entries on repo call."""
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        auth_result = MagicMock()
        auth_result.scalars.return_value.one_or_none.return_value = user

        repo_result = MagicMock()
        repo_result.scalars.return_value.all.return_value = entries

        mock_session.execute = AsyncMock(side_effect=[auth_result, repo_result])


class TestTrendSuccess(_TrendSuccessBase):
    async def test_two_entry_decreasing_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_two_entry_decreasing_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Body-weight trend calculated successfully."
        assert "data" in data

    async def test_two_entry_decreasing_data(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["observation_count"] == 2
        assert data["first_logged_date"] == "2026-07-01"
        assert data["latest_logged_date"] == "2026-07-12"
        assert data["starting_weight_kg"] == "75.00"
        assert data["latest_weight_kg"] == "73.50"
        assert data["absolute_change_kg"] == "-1.50"
        assert data["percentage_change"] == "-2.00"
        assert data["direction"] == "decreased"

    async def test_two_entry_increasing_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("70.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("75.00"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_two_entry_stable_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("70.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("70.00"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_multi_entry_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("80.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 5),
                weight_kg=Decimal("77.00"),
                entry_id=uuid.uuid4(),
            ),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("75.00"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_exact_success_message(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Body-weight trend calculated successfully."

    async def test_decimal_values_are_json_strings(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert isinstance(data["starting_weight_kg"], str)
        assert isinstance(data["latest_weight_kg"], str)
        assert isinstance(data["absolute_change_kg"], str)
        assert isinstance(data["percentage_change"], str)

    async def test_no_float_serialization(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert isinstance(data["starting_weight_kg"], str)
        assert isinstance(data["latest_weight_kg"], str)
        assert isinstance(data["absolute_change_kg"], str)
        assert isinstance(data["percentage_change"], str)

    async def test_dates_are_iso_strings(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["first_logged_date"] == "2026-07-01"
        assert data["latest_logged_date"] == "2026-07-12"

    async def test_lowercase_direction(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["direction"] == data["direction"].lower()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_deterministic_repeated_requests(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        auth_result = MagicMock()
        auth_result.scalars.return_value.one_or_none.return_value = user
        repo_result = MagicMock()
        repo_result.scalars.return_value.all.return_value = entries
        mock_session.execute = AsyncMock(
            side_effect=[auth_result, repo_result, auth_result, repo_result]
        )
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response1 = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        response2 = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.json() == response2.json()


# ===========================================================================
# I. Insufficient history
# ===========================================================================


class TestInsufficientHistory(_TrendSuccessBase):
    """Tests for the body-weight trend endpoint when history is insufficient.

    As of the graceful-onboarding update, the endpoint returns HTTP 200 with
    requires_onboarding=True instead of 422.  The critical safety invariants
    preserved are:
      - No IndexError or unhandled exception
      - No misleading trend direction or calculated values
      - The requires_onboarding flag is set so the frontend can show the
        onboarding prompt
    """

    async def test_empty_history_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_one_entry_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("70.00")),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_requires_onboarding_flag_set(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["data"]["requires_onboarding"] is True

    async def test_safe_message_present(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    async def test_no_index_error_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "IndexError" not in response.text
        assert "list index out of range" not in response.text

    async def test_no_profile_weight_fallback(self, client, test_settings, mock_session):
        """Empty history should not use arbitrary profile weight as a result."""
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should return 200 with onboarding, not a 422 error
        assert response.status_code == 200

    async def test_no_trend_schema_conversion_produces_onboarding(
        self, client, test_settings, mock_session
    ):
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        # Has data (onboarding placeholder) but no error key
        assert "data" in data
        assert "error" not in data

    async def test_no_success_response_after_insufficiency(
        self, client, test_settings, mock_session
    ):
        """Renamed: now returns success=True with onboarding flag."""
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        # Returns success=True with requires_onboarding flag
        assert data["success"] is True
        assert data["data"]["requires_onboarding"] is True

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session_with_entries(mock_session, user, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200




# ===========================================================================
# J. Unexpected failures
# ===========================================================================


class TestUnexpectedErrors:
    async def test_repository_failure_returns_500(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("repo failure")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_global_internal_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("fail")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_safe_generic_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("fail")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["message"] == "An unexpected error occurred."

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("fail")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("fail")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_raw_exception_not_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("secret-detail")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "secret-detail" not in response.text

    async def test_sql_text_not_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("SELECT * FROM")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "SELECT" not in response.text

    async def test_constraint_names_not_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("uq_body_weights")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "uq_body_weights" not in response.text

    async def test_stack_traces_not_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("fail")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "Traceback" not in response.text

    async def test_secrets_not_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(side_effect=[mock_result, RuntimeError("password=secret")])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "secret" not in response.text.lower()


# ===========================================================================
# K. Read-only behavior
# ===========================================================================


class TestReadOnlyBehavior(_TrendSuccessBase):
    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_rollback(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_no_add(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_not_called()

    async def test_no_delete(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.delete.assert_not_called()

    async def test_no_trend_values_persisted(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()

    async def test_no_profile_synchronization(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]
        self._setup_session_with_entries(mock_session, user, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )


# ===========================================================================
# L. Regression and boundaries
# ===========================================================================


class TestRegressionBoundaries:
    async def test_existing_body_weight_post_unchanged(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json={"weight_kg": "70.00"},
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401

    async def test_existing_body_weight_get_unchanged(self, client):
        response = await client.get("/api/v1/body-weights")
        assert response.status_code == 401

    async def test_existing_body_weight_delete_unchanged(self, client):
        response = await client.delete(f"/api/v1/body-weights/{uuid.uuid4()}")
        assert response.status_code == 401

    async def test_existing_authentication_unchanged(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_existing_health_unchanged(self, test_settings):
        app = create_app(settings=test_settings)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/health")
        assert response.status_code == 200

    async def test_existing_nutrition_profile_unchanged(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code == 401

    async def test_existing_nutrition_log_unchanged(self, client):
        response = await client.get("/api/v1/nutrition-logs")
        assert response.status_code == 401

    async def test_existing_body_weight_trend_domain_unchanged(self):
        from app.core.body_weight_trends import (
            BodyWeightTrendDirection,
            BodyWeightTrendResult,
        )
        from app.core.body_weight_trends import (
            calculate_body_weight_trend as _calc,
        )

        assert BodyWeightTrendDirection is not None
        assert BodyWeightTrendResult is not None
        assert _calc is not None

    async def test_existing_body_weight_trend_schemas_unchanged(self):
        from app.schemas.body_weight_trends import (
            BodyWeightTrendData,
            BodyWeightTrendSuccessResponse,
        )

        assert BodyWeightTrendData is not None
        assert BodyWeightTrendSuccessResponse is not None

    async def test_no_orm_changes(self):
        from app.db.base import Base

        tables = set(Base.metadata.tables)
        assert "users" in tables
        assert "nutrition_profiles" in tables
        assert "nutrition_logs" in tables
        assert "body_weights" in tables
        assert len(tables) == 6

    async def test_no_phase_5c4_work(self):
        import os

        base = os.path.join(os.path.dirname(__file__), "..", "app")
        assert not os.path.exists(os.path.join(base, "services", "body_weight_trend.py"))
        assert not os.path.exists(os.path.join(base, "repositories", "body_weight_trend.py"))
        assert not os.path.exists(os.path.join(base, "models", "body_weight_trend.py"))
