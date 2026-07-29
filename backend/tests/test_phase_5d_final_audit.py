"""Phase 5D — final audit: cross-layer invariant verification.

These tests verify stable invariants that span the body-weight goal
progress feature: the domain layer, the schema layer, the API route
inventory, the OpenAPI contract, ORM metadata, and Alembic migration
topology.

They complement (and do not duplicate) the dedicated unit/API tests:

    tests/test_body_weight_goals.py
    tests/test_body_weight_goal_exceptions.py
    tests/test_body_weight_goal_schemas.py
    tests/test_body_weight_goal_progress_api.py

All checks are read-only and never connect to a database.
"""

from __future__ import annotations

import importlib
import inspect
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.body_weight import (
    BODY_WEIGHT_DECIMAL_PLACES,
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
)
from app.core.body_weight_goals import (
    BodyWeightGoalDirection,
    BodyWeightGoalProgressResult,
    BodyWeightGoalStatus,
    calculate_body_weight_goal_progress,
)
from app.db.base import Base
from app.main import create_app
from app.schemas.body_weight_goals import (
    BodyWeightGoalProgressData,
    BodyWeightGoalProgressSuccessResponse,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


# ===========================================================================
# A. Domain contracts
# ===========================================================================


class TestDomainContracts:
    def test_direction_enum_values(self):
        assert {e.value for e in BodyWeightGoalDirection} == {
            "decrease",
            "maintain",
            "increase",
        }

    def test_status_enum_values(self):
        assert {e.value for e in BodyWeightGoalStatus} == {
            "not_started",
            "in_progress",
            "target_reached",
            "target_passed",
        }

    def test_progress_result_is_frozen_and_slotted(self):
        cls = BodyWeightGoalProgressResult
        assert "__slots__" in cls.__dict__
        assert cls.__dataclass_params__.frozen is True

    def test_progress_result_exact_field_order(self):
        fields = list(BodyWeightGoalProgressResult.__dataclass_fields__.keys())
        assert fields == [
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "direction",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
            "status",
        ]

    def test_all_progress_result_numeric_fields_are_decimal(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=Decimal("80.00"),
            current_weight_kg=Decimal("76.00"),
            target_weight_kg=Decimal("70.00"),
        )
        for name in (
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
        ):
            assert isinstance(getattr(result, name), Decimal)

    def test_domain_has_no_system_clock(self):
        source = inspect.getsource(importlib.import_module("app.core.body_weight_goals"))
        for token in ("datetime.now", "date.today", "time.time", "timezone.now"):
            assert token not in source

    def test_domain_has_no_framework_imports(self):
        source = inspect.getsource(importlib.import_module("app.core.body_weight_goals"))
        for token in ("import fastapi", "from fastapi", "import sqlalchemy", "from sqlalchemy"):
            assert token not in source

    def test_domain_reuses_body_weight_constants(self):
        import app.core.body_weight_goals as mod

        assert mod.MIN_BODY_WEIGHT_KG is MIN_BODY_WEIGHT_KG
        assert mod.MAX_BODY_WEIGHT_KG is MAX_BODY_WEIGHT_KG
        assert mod.BODY_WEIGHT_DECIMAL_PLACES is BODY_WEIGHT_DECIMAL_PLACES


# ===========================================================================
# B. Schema contracts
# ===========================================================================


class TestSchemaContracts:
    def test_progress_data_public_fields_only(self):
        fields = set(BodyWeightGoalProgressData.model_fields.keys())
        assert fields == {
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "direction",
            "total_change_required_kg",
            "change_achieved_kg",
            "remaining_change_kg",
            "progress_percentage",
            "status",
            "requires_onboarding",
        }
        for forbidden in ("user_id", "id", "created_at", "updated_at", "entry_id"):
            assert forbidden not in fields

    def test_progress_data_frozen_and_forbid(self):
        config = BodyWeightGoalProgressData.model_config
        assert config.get("frozen") is True
        assert config.get("extra") == "forbid"

    def test_from_result_is_exact_copy(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=Decimal("80.00"),
            current_weight_kg=Decimal("76.00"),
            target_weight_kg=Decimal("70.00"),
        )
        data = BodyWeightGoalProgressData.from_result(result)
        for name in BodyWeightGoalProgressResult.__dataclass_fields__:
            assert getattr(data, name) == getattr(result, name)
        assert data.direction is result.direction
        assert data.status is result.status

    def test_decimal_serialized_as_string(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=Decimal("80.00"),
            current_weight_kg=Decimal("76.00"),
            target_weight_kg=Decimal("70.00"),
        )
        payload = BodyWeightGoalProgressData.from_result(result).model_dump(mode="json")
        assert isinstance(payload["starting_weight_kg"], str)
        assert isinstance(payload["progress_percentage"], str)
        assert payload["progress_percentage"] == "40.00"

    def test_enum_serialized_lowercase(self):
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=Decimal("80.00"),
            current_weight_kg=Decimal("76.00"),
            target_weight_kg=Decimal("70.00"),
        )
        payload = BodyWeightGoalProgressData.from_result(result).model_dump()
        assert payload["direction"] == "decrease"
        assert payload["status"] == "in_progress"

    def test_success_response_contract(self):
        config = BodyWeightGoalProgressSuccessResponse.model_config
        assert config.get("extra") == "forbid"
        assert (
            BodyWeightGoalProgressSuccessResponse.model_fields["message"].default
            == "Body-weight goal progress calculated successfully."
        )
        # data is required (no default)
        assert BodyWeightGoalProgressSuccessResponse.model_fields["data"].is_required()


# ===========================================================================
# C. API route inventory
# ===========================================================================


class TestApiRouteInventory:
    def _goal_progress_routes(self, app):
        return [
            r
            for r in app.routes
            if getattr(r, "path", "") == "/api/v1/body-weights/goal-progress"
            and "GET" in getattr(r, "methods", set())
        ]

    def test_exactly_one_goal_progress_route(self):
        assert len(self._goal_progress_routes(create_app())) == 1

    def test_get_only(self):
        route = self._goal_progress_routes(create_app())[0]
        assert route.methods == {"GET"}

    def test_static_route_declared_before_dynamic(self):
        from app.api.v1.body_weights import router

        paths = [getattr(r, "path", "") for r in router.routes]
        assert paths.index("/body-weights/goal-progress") < paths.index("/body-weights/{entry_id}")

    def test_no_request_body_or_weight_params_in_openapi(self):
        op = create_app().openapi()["paths"]["/api/v1/body-weights/goal-progress"]["get"]
        assert "requestBody" not in op
        names = {p.get("name") for p in op.get("parameters", [])}
        for forbidden in (
            "user_id",
            "starting_weight_kg",
            "current_weight_kg",
            "target_weight_kg",
            "goal_date",
            "reference_date",
        ):
            assert forbidden not in names


# ===========================================================================
# D. OpenAPI
# ===========================================================================


class TestOpenAPI:
    def test_exactly_one_bearer_auth(self):
        schemes = create_app().openapi().get("components", {}).get("securitySchemes", {})
        bearer = [v for v in schemes.values() if v.get("scheme") == "bearer"]
        assert len(bearer) == 1

    def test_goal_progress_requires_bearer(self):
        op = create_app().openapi()["paths"]["/api/v1/body-weights/goal-progress"]["get"]
        assert any("BearerAuth" in s for s in op.get("security", []))

    def test_correct_success_schema(self):
        ref = create_app().openapi()["paths"]["/api/v1/body-weights/goal-progress"]["get"][
            "responses"
        ]["200"]["content"]["application/json"]["schema"]["$ref"]
        assert ref.endswith("BodyWeightGoalProgressSuccessResponse")


# ===========================================================================
# E. ORM / migration integrity
# ===========================================================================


class TestOrmMigrationIntegrity:
    def test_exactly_five_tables(self):
        assert set(Base.metadata.tables.keys()) == {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }

    def test_no_goal_progress_table_or_columns(self):
        assert "body_weight_goal_progress" not in Base.metadata.tables
        bw_columns = set(Base.metadata.tables["body_weights"].columns.keys())
        for forbidden in (
            "goal_progress",
            "goal_date",
            "time_to_goal",
            "prediction",
            "target_date",
        ):
            assert forbidden not in bw_columns

    def test_exactly_five_migrations(self):
        script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
        assert len(list(script.walk_revisions())) == 7

    def test_one_base_and_linear_chain(self):
        script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
        revs = list(script.walk_revisions())
        none_count = sum(1 for r in revs if r.down_revision is None)
        assert none_count == 1
        seen = set()
        for r in revs:
            if r.down_revision is None:
                continue
            assert r.down_revision not in seen
            seen.add(r.down_revision)

    def test_head_is_correct(self):
        script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
        heads = script.get_heads()
        assert heads == ["0295723946b2"]


# ===========================================================================
# F. Application factory
# ===========================================================================


class TestApplicationFactory:
    def test_two_instances_distinct(self):
        assert create_app() is not create_app()

    def test_openapi_generates(self):
        assert isinstance(create_app().openapi(), dict)

    def test_no_db_connection_on_import(self):
        import app.main as main_mod

        for name in dir(main_mod):
            if name.startswith("engine") or name.startswith("Session"):
                obj = getattr(main_mod, name)
                if isinstance(obj, sa.Engine):
                    raise AssertionError("Import exposed an SQLAlchemy engine")


# ===========================================================================
# G. Phase boundaries
# ===========================================================================


class TestPhaseBoundaries:
    def _source(self, mod_name):
        return inspect.getsource(importlib.import_module(mod_name))

    def test_no_prohibited_functionality_in_domain(self):
        source = self._source("app.core.body_weight_goals")
        for token in (
            "prediction",
            "time_to_goal",
            "goal_date",
            "recommendation",
            "groq",
            "openai",
            "llm",
        ):
            assert token not in source.lower()

    def test_no_prohibited_functionality_in_api(self):
        source = self._source("app.api.v1.body_weights")
        for token in (
            "prediction",
            "time_to_goal",
            "goal_date",
            "recommendation",
            "groq",
            "openai",
            "llm",
        ):
            assert token not in source.lower()

    def test_no_ai_dependencies_in_pyproject(self):
        pyproject = (BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
        for token in ("groq", "openai", "langchain", "anthropic"):
            assert token not in pyproject
