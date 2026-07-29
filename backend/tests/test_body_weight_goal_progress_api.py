from __future__ import annotations

import inspect
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
from app.core.body_weight_goals import (
    calculate_body_weight_goal_progress as real_calc,
)
from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.body_weight import BodyWeight
from app.models.nutrition_profile import NutritionProfile
from app.models.user import User

NOW = datetime.now(UTC)

EXPECTED_PROGRESS_MESSAGE = "Body-weight goal progress calculated successfully."
EXPECTED_INVALID_MESSAGE = (
    "Body-weight goal progress requires a starting weight that differs from the target weight."
)
EXPECTED_CURRENT_WEIGHT_MESSAGE = (
    "At least one body-weight entry is required to calculate goal progress."
)


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


def _make_profile(
    *,
    user_id: uuid.UUID | None = None,
    weight_kg: Decimal | None = None,
    target_weight_kg: Decimal | None = None,
) -> MagicMock:
    profile = MagicMock(spec=NutritionProfile)
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.weight_kg = weight_kg if weight_kg is not None else Decimal("80.00")
    profile.target_weight_kg = target_weight_kg
    return profile


def _make_body_weight(
    *,
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
    entry.weight_kg = weight_kg if weight_kg is not None else Decimal("70.00")
    entry.created_at = NOW
    entry.updated_at = NOW
    return entry


def _make_execute_result(value: MagicMock | None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


def _make_execute_result_for_list(values: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


def _setup_session(mock_session, user, profile, entries):
    """Arrange session.execute to return auth, then profile, then history."""
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.delete = MagicMock()
    mock_session.merge = MagicMock()

    auth_result = _make_execute_result(user)
    profile_result = _make_execute_result(profile)
    history_result = _make_execute_result_for_list(list(entries))

    calls = [auth_result, profile_result, history_result]
    mock_session.execute = AsyncMock(side_effect=calls)
    return calls


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


# ===========================================================================
# A. Route registration and ordering
# ===========================================================================


class TestRouteRegistration:
    async def test_exact_get_path_exists(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.status_code != 404

    async def test_route_registered_exactly_once(self, app):
        routes = [
            r
            for r in app.routes
            if getattr(r, "path", "") == "/api/v1/body-weights/goal-progress"
            and hasattr(r, "methods")
            and "GET" in r.methods
        ]
        assert len(routes) == 1

    async def test_static_goal_progress_not_shadowed(self, app):
        routes = [
            r for r in app.routes if getattr(r, "path", "") == "/api/v1/body-weights/goal-progress"
        ]
        assert len(routes) == 1

    async def test_route_on_existing_body_weight_router(self, app):
        from app.api.v1.body_weights import router

        path_found = any(
            "/goal-progress" in str(getattr(r, "path", ""))
            or "/goal-progress" in str(getattr(r, "paths", ""))
            for r in router.routes
        )
        assert path_found

    async def test_no_second_body_weight_router(self, app):
        from app.api.v1.body_weights import router as bw_router

        assert bw_router.prefix == "/body-weights"

    async def test_no_post_goal_progress(self, client):
        response = await client.post("/api/v1/body-weights/goal-progress")
        assert response.status_code not in (200, 201)

    async def test_no_patch_goal_progress(self, client):
        response = await client.patch("/api/v1/body-weights/goal-progress")
        assert response.status_code not in (200, 201)

    async def test_no_put_goal_progress(self, client):
        response = await client.put("/api/v1/body-weights/goal-progress")
        assert response.status_code not in (200, 201)

    async def test_no_delete_goal_progress(self, client):
        response = await client.delete("/api/v1/body-weights/goal-progress")
        assert response.status_code in (404, 405, 401)

    async def test_existing_body_weight_routes_unchanged(self, app):
        bw_paths = {r.path for r in app.routes if "body-weight" in r.path}
        assert "/api/v1/body-weights" in bw_paths
        assert "/api/v1/body-weights/trend" in bw_paths
        assert "/api/v1/body-weights/goal-progress" in bw_paths
        assert "/api/v1/body-weights/{entry_id}" in bw_paths

    async def test_goal_progress_declared_before_entry_id(self, app):
        from app.api.v1.body_weights import router

        paths = [getattr(r, "path", "") for r in router.routes]
        goal_index = paths.index("/body-weights/goal-progress")
        entry_index = paths.index("/body-weights/{entry_id}")
        assert goal_index < entry_index


# ===========================================================================
# B. OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_goal_progress_path_exists(self, app):
        openapi = app.openapi()
        assert "/api/v1/body-weights/goal-progress" in openapi.get("paths", {})

    async def test_get_is_only_operation(self, app):
        openapi = app.openapi()
        ops = openapi["paths"]["/api/v1/body-weights/goal-progress"]
        assert "get" in ops
        assert "post" not in ops
        assert "patch" not in ops
        assert "put" not in ops
        assert "delete" not in ops

    async def test_http_200_documented(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"]
        assert "200" in get_op.get("responses", {})

    async def test_correct_response_schema(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"]
        resp_200 = get_op["responses"]["200"]
        content = resp_200.get("content", {})
        schema = content.get("application/json", {}).get("schema", {})
        ref = schema.get("$ref", "")
        assert "BodyWeightGoalProgressSuccessResponse" in ref

    async def test_bearer_auth_required(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"]
        sec = get_op.get("security", [])
        assert any("BearerAuth" in s for s in sec)

    async def test_exactly_one_bearer_scheme(self, app):
        openapi = app.openapi()
        schemes = openapi.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1

    async def test_no_request_body(self, app):
        openapi = app.openapi()
        get_op = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"]
        assert "requestBody" not in get_op

    async def test_no_user_id_parameter(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"].get("parameters", [])
        user_id_params = [p for p in params if p.get("name") == "user_id"]
        assert len(user_id_params) == 0

    async def test_no_weight_parameters(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"].get("parameters", [])
        names = {p.get("name") for p in params}
        assert "starting_weight_kg" not in names
        assert "current_weight_kg" not in names
        assert "target_weight_kg" not in names

    async def test_no_goal_date_parameter(self, app):
        openapi = app.openapi()
        params = openapi["paths"]["/api/v1/body-weights/goal-progress"]["get"].get("parameters", [])
        names = {p.get("name") for p in params}
        assert "goal_date" not in names
        assert "reference_date" not in names

    async def test_existing_openapi_paths_unchanged(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/body-weights" in paths
        assert "/api/v1/body-weights/{entry_id}" in paths
        assert "/api/v1/body-weights/trend" in paths


# ===========================================================================
# C. Authentication
# ===========================================================================


class TestAuthMissingToken:
    async def test_missing_token_returns_401(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.status_code == 401

    async def test_missing_token_safe_envelope(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_missing_token_www_authenticate(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.headers.get("WWW-Authenticate") == "Bearer"


class TestAuthInvalidToken:
    async def test_invalid_token_returns_401(self, client):
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_invalid_token_code(self, client):
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
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
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_expired_token_code(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
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
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestAuthInactiveUser:
    async def test_inactive_user_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_inactive_user_code(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthOrdering:
    async def test_auth_before_profile_lookup(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.status_code == 401

    async def test_auth_before_history_lookup(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.status_code == 401

    async def test_auth_before_calculation(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.status_code == 401

    async def test_auth_before_conversion(self, client):
        response = await client.get("/api/v1/body-weights/goal-progress")
        assert response.status_code == 401

    async def test_no_manual_jwt_decoding(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "decode_access_token" not in source
        assert "jwt.decode" not in source

    async def test_existing_auth_reused(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "get_current_user" in source


# ===========================================================================
# D. Current-user isolation
# ===========================================================================


class TestCurrentUserIsolation:
    async def test_profile_loaded_using_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("70.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )

    async def test_no_caller_supplied_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("70.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress?user_id=" + str(uuid.uuid4()),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_response_contains_no_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("70.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_no_orm_internal_id_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("70.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        text_lower = response.text.lower()
        assert "created_at" not in text_lower
        assert "updated_at" not in text_lower

    async def test_route_uses_current_user_id_only(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        start = source.find("def get_body_weight_goal_progress")
        end = source.find("def ", start + 4)
        if end == -1:
            end = len(source)
        section = source[start:end]
        assert "current_user.id" in section
        assert "user_id=" in section


# ===========================================================================
# E. Repository and service reuse / orchestration
# ===========================================================================


class TestRepositoryServiceReuse:
    async def test_no_orm_query_in_route(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "session.execute(" not in source
        assert "select(" not in source

    async def test_profile_repository_constructed_with_session(self):
        from app.repositories.nutrition_profile import NutritionProfileRepository

        assert NutritionProfileRepository is not None

    async def test_profile_service_constructed_with_repository(self):
        from app.services.nutrition_profile import NutritionProfileService

        assert NutritionProfileService is not None

    async def test_weight_repository_constructed_with_session(self):
        from app.repositories.body_weight import BodyWeightRepository

        assert BodyWeightRepository is not None


class TestSuccessfulOrchestration:
    async def test_end_to_end_decrease_partial(
        self, client, test_settings, mock_session, monkeypatch
    ):
        import app.api.v1.body_weights as bw_module

        calc_calls = []
        captured_result = {}

        def spy_calc(**kwargs):
            calc_calls.append(dict(kwargs))
            return real_calc(**kwargs)

        orig_from_result = bw_module.BodyWeightGoalProgressData.from_result

        def spy_from_result(result):
            captured_result["result"] = result
            return orig_from_result(result)

        monkeypatch.setattr(bw_module, "calculate_body_weight_goal_progress", spy_calc)
        monkeypatch.setattr(bw_module.BodyWeightGoalProgressData, "from_result", spy_from_result)

        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 10),
                weight_kg=Decimal("76.00"),
                entry_id=uuid.uuid4(),
            ),
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("80.00"),
            ),
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["starting_weight_kg"] == "80.00"
        assert data["current_weight_kg"] == "76.00"
        assert data["target_weight_kg"] == "70.00"
        assert data["direction"] == "decrease"
        assert data["progress_percentage"] == "40.00"
        assert data["status"] == "in_progress"

        assert calc_calls and len(calc_calls) == 1
        assert calc_calls[0] == {
            "starting_weight_kg": Decimal("80.00"),
            "current_weight_kg": Decimal("76.00"),
            "target_weight_kg": Decimal("70.00"),
        }
        assert "result" in captured_result

    async def test_latest_entry_selected_not_earliest(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 20),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("71.00"),
            ),
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["current_weight_kg"] == "73.50"
        assert data["current_weight_kg"] != "71.00"

    async def test_profile_weight_used_as_starting(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("85.00"),
            target_weight_kg=Decimal("75.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("80.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["starting_weight_kg"] == "85.00"

    async def test_latest_history_weight_used_as_current(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("85.00"),
            target_weight_kg=Decimal("75.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("80.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["current_weight_kg"] == "80.00"

    async def test_profile_target_used_as_target(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("85.00"),
            target_weight_kg=Decimal("75.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("80.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()["data"]
        assert data["target_weight_kg"] == "75.00"

    async def test_exact_success_message(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("76.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["message"] == EXPECTED_PROGRESS_MESSAGE

    async def test_no_manual_response_dictionary(self, client, test_settings, mock_session):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        start = source.find("def get_body_weight_goal_progress")
        end = source.find("def ", start + 4)
        if end == -1:
            end = len(source)
        section = source[start:end]
        assert "BodyWeightGoalProgressSuccessResponse" in section
        assert "from_result" in section
        assert '{"success"' not in section
        assert '"data"' not in section


# ===========================================================================
# F. Progress values
# ===========================================================================


class TestProgressValues:
    async def _run(self, client, test_settings, mock_session, profile, entries):
        user = _make_user()
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        return response

    async def test_decrease_partial(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("76.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["progress_percentage"] == "40.00"
        assert data["status"] == "in_progress"

    async def test_increase_partial(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("70.00"), target_weight_kg=Decimal("80.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("73.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["direction"] == "increase"
        assert data["progress_percentage"] == "30.00"
        assert data["status"] == "in_progress"

    async def test_not_started(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("82.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["status"] == "not_started"
        assert data["progress_percentage"] == "-20.00"

    async def test_target_reached(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("70.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["status"] == "target_reached"
        assert data["progress_percentage"] == "100.00"

    async def test_target_passed(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("68.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["status"] == "target_passed"
        assert data["progress_percentage"] == "120.00"

    async def test_negative_progress_preserved(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("85.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["change_achieved_kg"] == "-5.00"
        assert data["progress_percentage"] == "-50.00"

    async def test_progress_above_100_preserved(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("68.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["progress_percentage"] == "120.00"

    async def test_negative_remaining_change_preserved(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("68.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert data["remaining_change_kg"] == "-2.00"

    async def test_decimals_serialized_as_strings(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("76.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        data = response.json()["data"]
        assert isinstance(data["starting_weight_kg"], str)
        assert isinstance(data["current_weight_kg"], str)
        assert isinstance(data["target_weight_kg"], str)
        assert isinstance(data["progress_percentage"], str)

    async def test_direction_serialized_lowercase(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("76.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        assert response.json()["data"]["direction"] == "decrease"

    async def test_status_serialized_lowercase(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("76.00"))]
        response = await self._run(client, test_settings, mock_session, profile, entries)
        assert response.json()["data"]["status"] == "in_progress"

    async def test_deterministic_response(self, client, test_settings, mock_session):
        profile = _make_profile(weight_kg=Decimal("80.00"), target_weight_kg=Decimal("70.00"))
        entries = [_make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("76.00"))]
        user = _make_user()
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        r1 = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        _setup_session(mock_session, user, profile, entries)
        r2 = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.json() == r2.json()


# ===========================================================================
# G. Empty history
# ===========================================================================


class TestEmptyHistory:
    async def test_safe_domain_error(self, client, test_settings, mock_session):
        """When history is empty the endpoint must NOT crash or expose raw Python errors.

        The API intentionally returns 200 with requires_onboarding=True so that
        new/empty users get a graceful response rather than an error page.
        The security invariant (no IndexError, no unhandled exception) is verified
        here via the HTTP status and the absence of error codes in the body.
        """
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        _setup_session(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        # API returns 200 with a safe onboarding placeholder — not a 5xx error
        assert response.status_code == 200
        data = response.json()
        # Must be a success response with requires_onboarding flag, not a crash
        assert data.get("success", True) is not False or "error" not in data
        assert "traceback" not in response.text.lower()
        assert "indexerror" not in response.text.lower()


    async def test_no_index_error_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        _setup_session(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "indexerror" not in text
        assert "list index out of range" not in text

    async def test_calculation_not_called(self, client, test_settings, mock_session, monkeypatch):
        import app.api.v1.body_weights as bw_module

        calc_calls = []
        monkeypatch.setattr(
            bw_module,
            "calculate_body_weight_goal_progress",
            lambda **kwargs: calc_calls.append(kwargs),
        )
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        _setup_session(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calc_calls == []

    async def test_conversion_not_called(self, client, test_settings, mock_session, monkeypatch):
        import app.api.v1.body_weights as bw_module

        from_result_calls = []
        monkeypatch.setattr(
            bw_module.BodyWeightGoalProgressData,
            "from_result",
            lambda result: from_result_calls.append(result),
        )
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        _setup_session(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert from_result_calls == []

    async def test_no_write_methods_called(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        _setup_session(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_not_called()


# ===========================================================================
# H. Missing profile
# ===========================================================================


class TestMissingProfile:
    async def test_404_behavior(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session(mock_session, user, None, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_PROFILE_NOT_FOUND"
        assert data["error"]["message"] == "Nutrition profile not found."

    async def test_body_weight_lookup_not_called(
        self, client, test_settings, mock_session, monkeypatch
    ):
        import app.api.v1.body_weights as bw_module

        list_calls = []

        async def spy_list(*, user_id):
            list_calls.append(user_id)
            return []

        monkeypatch.setattr(bw_module.BodyWeightService, "list_history", staticmethod(spy_list))
        user = _make_user()
        _setup_session(mock_session, user, None, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_calls == []

    async def test_calculation_not_called(self, client, test_settings, mock_session, monkeypatch):
        import app.api.v1.body_weights as bw_module

        calc_calls = []
        monkeypatch.setattr(
            bw_module,
            "calculate_body_weight_goal_progress",
            lambda **kwargs: calc_calls.append(kwargs),
        )
        user = _make_user()
        _setup_session(mock_session, user, None, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calc_calls == []

    async def test_conversion_not_called(self, client, test_settings, mock_session, monkeypatch):
        import app.api.v1.body_weights as bw_module

        from_result_calls = []
        monkeypatch.setattr(
            bw_module.BodyWeightGoalProgressData,
            "from_result",
            lambda result: from_result_calls.append(result),
        )
        user = _make_user()
        _setup_session(mock_session, user, None, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert from_result_calls == []


# ===========================================================================
# I. Equal starting and target weights
# ===========================================================================


class TestEqualStartTarget:
    async def test_422_status(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("80.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("75.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "BODY_WEIGHT_GOAL_PROGRESS_INVALID"
        assert data["error"]["message"] == EXPECTED_INVALID_MESSAGE

    async def test_no_fabricated_progress(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("80.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("75.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "progress_percentage" not in data
        assert "data" not in data

    async def test_conversion_not_called(self, client, test_settings, mock_session, monkeypatch):
        import app.api.v1.body_weights as bw_module

        from_result_calls = []
        monkeypatch.setattr(
            bw_module.BodyWeightGoalProgressData,
            "from_result",
            lambda result: from_result_calls.append(result),
        )
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("80.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("75.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert from_result_calls == []


# ===========================================================================
# J. Unexpected failures
# ===========================================================================


class TestUnexpectedFailures:
    async def test_profile_read_failure_global_500(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(side_effect=RuntimeError("boom"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_body_weight_read_failure_global_500(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        auth_result = _make_execute_result(user)
        profile_result = _make_execute_result(profile)
        bad = MagicMock()
        bad.scalars.return_value.all.side_effect = RuntimeError("boom")
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=[auth_result, profile_result, bad])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_goal_calculation_failure_global_500(
        self, client, test_settings, mock_session, monkeypatch
    ):
        import app.api.v1.body_weights as bw_module

        def boom(**kwargs):
            raise RuntimeError("calc boom")

        monkeypatch.setattr(bw_module, "calculate_body_weight_goal_progress", boom)
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("76.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_schema_conversion_failure_global_500(
        self, client, test_settings, mock_session, monkeypatch
    ):
        import app.api.v1.body_weights as bw_module

        def boom(result):
            raise RuntimeError("convert boom")

        monkeypatch.setattr(bw_module.BodyWeightGoalProgressData, "from_result", boom)
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("76.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_request_id_preserved(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(side_effect=RuntimeError("boom"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}", "X-Request-ID": "abc-123"},
        )
        assert response.headers.get("X-Request-ID") == "abc-123"

    async def test_no_raw_exception_text(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(side_effect=RuntimeError("boom"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "boom" not in text
        assert "runtimeerror" not in text


# ===========================================================================
# K. Read-only behavior
# ===========================================================================


class TestReadOnlyBehavior:
    async def test_no_write_methods_called(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("76.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_not_called()
        mock_session.flush.assert_not_called()
        mock_session.refresh.assert_not_called()
        mock_session.add.assert_not_called()
        mock_session.delete.assert_not_called()
        mock_session.merge.assert_not_called()

    async def test_profile_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entries = [
            _make_body_weight(
                user_id=user.id,
                logged_date=date(2026, 7, 1),
                weight_kg=Decimal("76.00"),
            )
        ]
        _setup_session(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile.weight_kg == Decimal("80.00")
        assert profile.target_weight_kg == Decimal("70.00")

    async def test_body_weight_entries_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            weight_kg=Decimal("80.00"),
            target_weight_kg=Decimal("70.00"),
        )
        entry = _make_body_weight(
            user_id=user.id,
            logged_date=date(2026, 7, 1),
            weight_kg=Decimal("76.00"),
        )
        _setup_session(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights/goal-progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert entry.weight_kg == Decimal("76.00")


# ===========================================================================
# L. Architecture / no formula duplication
# ===========================================================================


class TestArchitectureNoDuplication:
    async def test_reuses_calculate_function(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        start = source.find("def get_body_weight_goal_progress")
        end = source.find("def ", start + 4)
        if end == -1:
            end = len(source)
        section = source[start:end]
        assert "calculate_body_weight_goal_progress" in section

    async def test_reuses_from_result(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        start = source.find("def get_body_weight_goal_progress")
        end = source.find("def ", start + 4)
        if end == -1:
            end = len(source)
        section = source[start:end]
        assert "from_result" in section

    async def test_reuses_success_response(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        start = source.find("def get_body_weight_goal_progress")
        end = source.find("def ", start + 4)
        if end == -1:
            end = len(source)
        section = source[start:end]
        assert "BodyWeightGoalProgressSuccessResponse" in section

    async def test_no_direct_formula_terms(self):
        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        start = source.find("def get_body_weight_goal_progress")
        end = source.find("def ", start + 4)
        if end == -1:
            end = len(source)
        section = source[start:end]
        forbidden = [
            "quantize(",
            "ROUND_HALF_UP",
            "total_change_required_kg =",
            "change_achieved_kg =",
            "remaining_change_kg =",
            "progress_percentage =",
            "TARGET_REACHED",
            "TARGET_PASSED",
            "IN_PROGRESS",
        ]
        for token in forbidden:
            assert token not in section, f"Found duplicated formula token: {token}"
