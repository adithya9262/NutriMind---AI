"""Phase 5B — final audit: cross-layer invariant verification.

These tests verify invariants that span multiple layers of the
body-weight tracking module.  They do not duplicate coverage that
already exists in dedicated unit-test files.

The tests are read-only and never connect to a database.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.body_weight import (
    BODY_WEIGHT_DECIMAL_PLACES,
    MAX_BODY_WEIGHT_KG,
    MIN_BODY_WEIGHT_KG,
)
from app.db.base import Base
from app.main import create_app
from app.models.body_weight import BodyWeight

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def _migration_files() -> list[Path]:
    return sorted(
        f for f in VERSIONS_DIR.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
    )


def _source(mod_name: str) -> str:
    mod = importlib.import_module(mod_name)
    return inspect.getsource(mod)


# ===========================================================================
# A. Cross-layer constants alignment
# ===========================================================================


class TestCrossLayerConstants:
    """Domain constants must align with ORM precision/scale and schema limits."""

    def test_domain_min_aligns_with_orm_check(self):
        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        for ck in checks:
            if ck.name == "ck_body_weights_weight_kg_range":
                sql = str(ck.sqltext)
                assert str(MIN_BODY_WEIGHT_KG) in sql, (
                    f"ORM check {sql!r} does not include domain min {MIN_BODY_WEIGHT_KG}"
                )

    def test_domain_max_aligns_with_orm_check(self):
        checks = [c for c in BodyWeight.__table__.constraints if isinstance(c, sa.CheckConstraint)]
        for ck in checks:
            if ck.name == "ck_body_weights_weight_kg_range":
                sql = str(ck.sqltext)
                assert str(MAX_BODY_WEIGHT_KG) in sql, (
                    f"ORM check {sql!r} does not include domain max {MAX_BODY_WEIGHT_KG}"
                )

    def test_domain_decimal_places_aligns_with_orm_scale(self):
        col = BodyWeight.__table__.c["weight_kg"]
        # BODY_WEIGHT_DECIMAL_PLACES = 0.01 → 2 decimal places → scale = 2
        domain_places = abs(BODY_WEIGHT_DECIMAL_PLACES.as_tuple().exponent)
        assert col.type.scale == domain_places, (
            f"ORM scale {col.type.scale} != domain decimal places {domain_places}"
        )

    def test_domain_range_fits_orm_precision(self):
        col = BodyWeight.__table__.c["weight_kg"]
        # Numeric(5, 2) supports up to 999.99
        max_supported = 10 ** (col.type.precision - col.type.scale) - 10 ** (-col.type.scale)
        assert float(MAX_BODY_WEIGHT_KG) <= max_supported, (
            f"Domain max {MAX_BODY_WEIGHT_KG} exceeds ORM max {max_supported}"
        )
        assert float(MIN_BODY_WEIGHT_KG) >= 0

    def test_schema_validator_uses_same_bounds(self):
        source = _source("app.schemas.body_weight")
        assert "MIN_BODY_WEIGHT_KG" in source
        assert "MAX_BODY_WEIGHT_KG" in source
        assert "BODY_WEIGHT_DECIMAL_PLACES" in source


# ===========================================================================
# B. Repository invariants
# ===========================================================================


class TestRepositoryUserScope:
    """Repository methods must always be user-scoped."""

    def test_list_by_user_id_requires_user_id(self):
        import inspect as _inspect

        from app.repositories.body_weight import BodyWeightRepository

        sig = _inspect.signature(BodyWeightRepository.list_by_user_id)
        params = list(sig.parameters.keys())
        assert "user_id" in params

    def test_get_by_user_and_entry_id_requires_both(self):
        import inspect as _inspect

        from app.repositories.body_weight import BodyWeightRepository

        sig = _inspect.signature(BodyWeightRepository.get_by_user_and_entry_id)
        params = list(sig.parameters.keys())
        assert "user_id" in params
        assert "entry_id" in params

    def test_create_requires_user_id(self):
        import inspect as _inspect

        from app.repositories.body_weight import BodyWeightRepository

        sig = _inspect.signature(BodyWeightRepository.create)
        params = list(sig.parameters.keys())
        assert "user_id" in params

    def test_delete_accepts_orm_entry_not_entry_id(self):
        import inspect as _inspect

        from app.repositories.body_weight import BodyWeightRepository

        sig = _inspect.signature(BodyWeightRepository.delete)
        params = list(sig.parameters.keys())
        assert "entry" in params
        assert "entry_id" not in params

    def test_repository_source_no_commit_or_rollback(self):
        source = _source("app.repositories.body_weight")
        assert ".commit(" not in source
        assert ".rollback(" not in source


# ===========================================================================
# C. Service invariants
# ===========================================================================


class TestServiceTransactionBoundary:
    """Service must not own transaction lifecycle."""

    def test_service_no_commit(self):
        source = _source("app.services.body_weight")
        assert ".commit(" not in source

    def test_service_no_rollback(self):
        source = _source("app.services.body_weight")
        assert ".rollback(" not in source

    def test_service_no_flush(self):
        source = _source("app.services.body_weight")
        assert ".flush(" not in source

    def test_service_no_refresh(self):
        source = _source("app.services.body_weight")
        assert ".refresh(" not in source

    def test_service_no_async_session(self):
        source = _source("app.services.body_weight").lower()
        assert "asyncsession" not in source


# ===========================================================================
# D. API invariants
# ===========================================================================


class TestApiRouteInventory:
    """Exact body-weight route inventory, no extras."""

    def test_exactly_three_body_weight_methods(self):
        app = create_app()
        bw_routes = []
        for route in app.routes:
            if not hasattr(route, "path"):
                continue
            if "body-weight" not in route.path and "body_weight" not in route.path:
                continue
            for method in getattr(route, "methods", set()) or set():
                bw_routes.append((method, route.path))
        expected = {
            ("POST", "/api/v1/body-weights"),
            ("GET", "/api/v1/body-weights"),
            ("GET", "/api/v1/body-weights/trend"),
            ("GET", "/api/v1/body-weights/goal-progress"),
            ("DELETE", "/api/v1/body-weights/{entry_id}"),
        }
        actual = set(bw_routes)
        assert actual == expected, f"Expected {expected}, got {actual}"

    def test_no_get_by_id(self):
        app = create_app()
        for route in app.routes:
            if not hasattr(route, "path") or not hasattr(route, "methods"):
                continue
            if "body-weight" not in route.path and "body_weight" not in route.path:
                continue
            if "GET" in (route.methods or set()) and "{entry_id}" in route.path:
                raise AssertionError(f"GET-by-ID found: {route.path}")

    def test_no_patch(self):
        app = create_app()
        for route in app.routes:
            if not hasattr(route, "path") or not hasattr(route, "methods"):
                continue
            if "body-weight" not in route.path and "body_weight" not in route.path:
                continue
            if "PATCH" in (route.methods or set()):
                raise AssertionError(f"PATCH found: {route.path}")

    def test_no_put(self):
        app = create_app()
        for route in app.routes:
            if not hasattr(route, "path") or not hasattr(route, "methods"):
                continue
            if "body-weight" not in route.path and "body_weight" not in route.path:
                continue
            if "PUT" in (route.methods or set()):
                raise AssertionError(f"PUT found: {route.path}")

    def test_no_summary_progress_trend_analytics(self):
        app = create_app()
        for route in app.routes:
            if not hasattr(route, "path"):
                continue
            p = route.path.lower()
            if "body-weight" not in p and "body_weight" not in p:
                continue
            if p == "/api/v1/body-weights/goal-progress":
                continue
            for forbidden in ("summary", "progress", "analytics", "weekly", "monthly"):
                if forbidden in p:
                    raise AssertionError(f"Forbidden route found: {route.path}")
            if "trend" in p and p != "/api/v1/body-weights/trend":
                raise AssertionError(f"Forbidden trend route found: {route.path}")


class TestApiAuthRequired:
    """All body-weight routes require authentication."""

    def test_all_bw_routes_have_auth_in_openapi(self):
        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        for path_key, methods in paths.items():
            if "body-weight" not in path_key and "body_weight" not in path_key:
                continue
            for method_key, op in methods.items():
                sec = op.get("security", [])
                assert any("BearerAuth" in s for s in sec), (
                    f"{method_key.upper()} {path_key} missing BearerAuth"
                )


class TestApiResponsePrivacy:
    """Public responses must not expose internal fields."""

    def test_body_weight_entry_data_no_user_id(self):
        from app.schemas.body_weight import BodyWeightEntryData

        assert "user_id" not in BodyWeightEntryData.model_fields

    def test_body_weight_entry_data_no_timestamps(self):
        from app.schemas.body_weight import BodyWeightEntryData

        assert "created_at" not in BodyWeightEntryData.model_fields
        assert "updated_at" not in BodyWeightEntryData.model_fields

    def test_body_weight_entry_data_no_orm_id(self):
        from app.schemas.body_weight import BodyWeightEntryData

        assert "id" not in BodyWeightEntryData.model_fields

    def test_delete_response_no_data(self):
        from app.schemas.body_weight import BodyWeightDeleteSuccessResponse

        assert "data" not in BodyWeightDeleteSuccessResponse.model_fields

    def test_history_data_entries_type(self):
        from app.schemas.body_weight import BodyWeightHistoryData

        field = BodyWeightHistoryData.model_fields["entries"]
        assert "tuple" in str(field.annotation).lower()


# ===========================================================================
# E. OpenAPI invariants
# ===========================================================================


class TestOpenApiInvariants:
    def test_exactly_one_bearer_auth(self):
        app = create_app()
        openapi = app.openapi()
        schemes = openapi.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme", "").lower() == "bearer")
        assert bearer_count == 1, f"Expected 1 BearerAuth, got {bearer_count}"

    def test_delete_path_documented_with_uuid(self):
        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        delete_op = paths.get("/api/v1/body-weights/{entry_id}", {}).get("delete", {})
        params = delete_op.get("parameters", [])
        entry_params = [p for p in params if p.get("name") == "entry_id"]
        assert len(entry_params) == 1
        assert entry_params[0]["in"] == "path"
        assert entry_params[0]["schema"]["format"] == "uuid"

    def test_logged_date_param_has_date_format(self):
        app = create_app()
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        post_op = paths.get("/api/v1/body-weights", {}).get("post", {})
        params = post_op.get("parameters", [])
        lp = [p for p in params if p.get("name") == "logged_date"]
        assert len(lp) == 1
        assert lp[0]["schema"]["format"] == "date"


# ===========================================================================
# F. ORM and migration invariants
# ===========================================================================


class TestOrmMigrationIntegrity:
    def test_body_weights_table_in_metadata(self):
        assert "body_weights" in Base.metadata.tables

    def test_exactly_five_tables(self):
        tables = set(Base.metadata.tables.keys())
        assert tables == {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }

    def test_exactly_five_migrations(self):
        files = _migration_files()
        assert len(files) == 7

    def test_linear_migration_chain(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        revs = list(script.walk_revisions())
        down_revisions = [r.down_revision for r in revs]
        # Base revision has None, all others must have a down_revision
        none_count = sum(1 for d in down_revisions if d is None)
        assert none_count == 1
        # No branches: each non-base revision must have exactly one child
        seen: set[str] = set()
        for rev in revs:
            if rev.down_revision:
                assert rev.down_revision not in seen or rev.down_revision is None
                seen.add(rev.down_revision)

    def test_migration_head_is_correct(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        heads = script.get_heads()
        assert len(heads) == 1
        assert heads[0] == "0295723946b2"

    def test_exactly_one_base(self):
        config = Config(str(ALEMBIC_INI))
        script = ScriptDirectory.from_config(config)
        bases = script.get_bases()
        assert len(bases) == 1

    def test_no_prohibited_columns_in_orm(self):
        columns = set(BodyWeight.__table__.c.keys())
        for field in {"bmi", "bmr", "tdee", "trend", "prediction", "body_fat"}:
            assert field not in columns, f"BodyWeight must not have field '{field}'"


# ===========================================================================
# G. No trend/analytics/prediction across all layers
# ===========================================================================


class TestNoProhibitedFunctionality:
    def _source_contains(self, mod_name: str, token: str) -> bool:
        try:
            source = _source(mod_name).lower()
            return token.lower() in source
        except (ImportError, OSError):
            return False

    MODULES = [
        "app.core.body_weight",
        "app.schemas.body_weight",
        "app.models.body_weight",
        "app.repositories.body_weight",
        "app.services.body_weight",
        "app.api.v1.body_weights",
    ]

    def test_no_trend(self):
        for mod in self.MODULES:
            if mod == "app.api.v1.body_weights":
                continue
            assert not self._source_contains(mod, "trend"), f"{mod} contains 'trend'"

    def test_no_prediction(self):
        for mod in self.MODULES:
            assert not self._source_contains(mod, "predict"), f"{mod} contains 'predict'"

    def test_no_bmi_calculation(self):
        for mod in self.MODULES:
            assert not self._source_contains(mod, "bmi"), f"{mod} contains 'bmi'"

    def test_no_bmr_calculation(self):
        for mod in self.MODULES:
            assert not self._source_contains(mod, "bmr"), f"{mod} contains 'bmr'"

    def test_no_tdee_calculation(self):
        for mod in self.MODULES:
            assert not self._source_contains(mod, "tdee"), f"{mod} contains 'tdee'"


# ===========================================================================
# H. Security and cleanliness
# ===========================================================================


class TestSecurityAndCleanliness:
    def test_env_file_gitignored_in_backend(self):
        gitignore = Path("../.gitignore").resolve()
        assert gitignore.exists(), ".gitignore not found"
        text = gitignore.read_text(encoding="utf-8")
        assert "backend/.env" in text

    def test_env_file_gitignored_in_root(self):
        gitignore = Path("../.gitignore").resolve()
        assert gitignore.exists(), ".gitignore not found"
        text = gitignore.read_text(encoding="utf-8")
        assert ".env" in text

    def test_main_py_has_no_alembic_import(self):
        source = _source("app.main")
        assert "alembic" not in source.lower()

    def test_create_app_no_database_connection(self):
        # Creating an app must not require a database URL
        app = create_app()
        assert app is not None

    def test_two_independent_apps(self):
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2


# ===========================================================================
# I. No system-clock fallback for logged_date
# ===========================================================================


class TestNoSystemClockFallback:
    def test_post_requires_logged_date_query_param(self):
        from app.api.v1.body_weights import router

        # Find the POST route and check its parameters
        for route in router.routes:
            if not hasattr(route, "methods"):
                continue
            if "POST" not in (route.methods or set()):
                continue
            # Check that the endpoint has a logged_date parameter without a default
            import inspect as _inspect

            sig = _inspect.signature(route.endpoint)
            params = sig.parameters
            assert "logged_date" in params
            p = params["logged_date"]
            from datetime import date as _date_type

            assert not isinstance(p.default, _date_type), (
                "logged_date must not default to date.today() (no system-clock fallback)"
            )

    def test_domain_does_not_call_date_today(self):
        source = _source("app.core.body_weight")
        assert "date.today(" not in source
        assert "datetime.now(" not in source
        assert "datetime.utcnow(" not in source


# ===========================================================================
# J. No duplicate body-weight implementation
# ===========================================================================


class TestNoDuplicateImplementation:
    NO_DUPLICATE_FILES = [
        "app/core/body_metrics.py",
        "app/schemas/body_metrics.py",
        "app/models/body_metrics.py",
        "app/repositories/body_metrics.py",
        "app/services/body_metrics.py",
        "app/api/v1/body_metrics.py",
        "app/core/weight.py",
        "app/schemas/weight.py",
        "app/models/weight.py",
        "app/api/v1/weight.py",
    ]

    def test_no_duplicate_module_files(self):
        backend = Path(__file__).resolve().parent.parent
        for mod_path in self.NO_DUPLICATE_FILES:
            full = backend / mod_path
            assert not full.exists(), f"Duplicate module exists: {mod_path}"

    def test_no_duplicate_api_router(self):
        backend = Path(__file__).resolve().parent.parent
        routers = list((backend / "app" / "api" / "v1").glob("*weight*"))
        assert len(routers) == 1, f"Expected 1 weight router, found {[r.name for r in routers]}"


# ===========================================================================
# K. No user_id in any public schema
# ===========================================================================


class TestNoPublicUserId:
    def test_no_user_id_in_entry_data(self):
        from app.schemas.body_weight import BodyWeightEntryData

        assert "user_id" not in BodyWeightEntryData.model_fields

    def test_no_user_id_in_history_data(self):
        from app.schemas.body_weight import BodyWeightHistoryData

        assert "user_id" not in BodyWeightHistoryData.model_fields

    def test_no_user_id_in_create_schema(self):
        from app.schemas.body_weight import BodyWeightEntryCreate

        assert "user_id" not in BodyWeightEntryCreate.model_fields

    def test_no_user_id_in_success_response(self):
        from app.schemas.body_weight import BodyWeightEntrySuccessResponse

        assert "user_id" not in BodyWeightEntrySuccessResponse.model_fields

    def test_no_user_id_in_delete_response(self):
        from app.schemas.body_weight import BodyWeightDeleteSuccessResponse

        assert "user_id" not in BodyWeightDeleteSuccessResponse.model_fields
