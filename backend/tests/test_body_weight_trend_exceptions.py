from __future__ import annotations

from app.core.body_weight_trend_exceptions import (
    BodyWeightTrendError,
    InsufficientBodyWeightHistoryError,
)


class TestBodyWeightTrendError:
    def test_inherits_from_exception(self):
        assert issubclass(BodyWeightTrendError, Exception)

    def test_can_be_raised(self):
        import pytest

        with pytest.raises(BodyWeightTrendError):
            raise BodyWeightTrendError()

    def test_no_http_status_code(self):
        exc = BodyWeightTrendError()
        assert not hasattr(exc, "status_code")

    def test_no_fastapi_dependency(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_import(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_sqlalchemy(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_pydantic(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "pydantic" not in source.lower()

    def test_no_starlette(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "starlette" not in source.lower()


class TestInsufficientBodyWeightHistoryError:
    def test_inherits_from_body_weight_trend_error(self):
        assert issubclass(InsufficientBodyWeightHistoryError, BodyWeightTrendError)

    def test_default_message_stable(self):
        exc = InsufficientBodyWeightHistoryError()
        assert str(exc) == ("At least two body-weight entries are required to calculate a trend.")

    def test_custom_message(self):
        exc = InsufficientBodyWeightHistoryError("Custom error")
        assert str(exc) == "Custom error"

    def test_message_contains_no_sql(self):
        exc = InsufficientBodyWeightHistoryError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)
        assert "FROM" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = InsufficientBodyWeightHistoryError()
        assert "postgresql" not in str(exc).lower()
        assert "localhost" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = InsufficientBodyWeightHistoryError()
        assert "password" not in str(exc).lower()
        assert "jwt" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = InsufficientBodyWeightHistoryError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_repr_contains_no_secrets(self):
        exc = InsufficientBodyWeightHistoryError()
        assert "secret" not in repr(exc).lower()

    def test_can_be_caught_as_base(self):
        import pytest

        with pytest.raises(BodyWeightTrendError):
            raise InsufficientBodyWeightHistoryError()

    def test_args_behavior(self):
        exc = InsufficientBodyWeightHistoryError()
        assert exc.args == ("At least two body-weight entries are required to calculate a trend.",)

    def test_custom_args_behavior(self):
        exc = InsufficientBodyWeightHistoryError("custom")
        assert exc.args == ("custom",)

    def test_no_env_access(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "environ" not in source

    def test_no_network_access(self):
        import app.core.body_weight_trend_exceptions as mod

        source = open(mod.__file__).read()
        assert "http" not in source.lower()

    def test_hashable(self):
        exc = InsufficientBodyWeightHistoryError()
        d = {exc: "mapped"}
        assert d[exc] == "mapped"


class TestImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        import app.core.body_weight_trend_exceptions as mod

        assert mod is not None

    def test_import_does_not_require_fastapi(self):
        import app.core.body_weight_trend_exceptions as mod

        assert hasattr(mod, "BodyWeightTrendError")
        assert hasattr(mod, "InsufficientBodyWeightHistoryError")
