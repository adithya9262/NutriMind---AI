from __future__ import annotations

import pytest

from app.core.body_weight_exceptions import (
    BodyWeightError,
    DuplicateBodyWeightDateError,
    InvalidBodyWeightError,
)


class TestBodyWeightError:
    def test_inherits_from_exception(self):
        assert issubclass(BodyWeightError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(BodyWeightError):
            raise BodyWeightError()

    def test_no_http_status_code(self):
        exc = BodyWeightError()
        assert not hasattr(exc, "status_code")

    def test_no_fastapi_dependency(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_import(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_sqlalchemy(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_pydantic(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "pydantic" not in source.lower()

    def test_no_starlette(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "starlette" not in source.lower()


class TestInvalidBodyWeightError:
    def test_inherits_from_body_weight_error(self):
        assert issubclass(InvalidBodyWeightError, BodyWeightError)

    def test_default_message_stable(self):
        exc = InvalidBodyWeightError()
        assert str(exc) == "The body-weight entry contains invalid data."

    def test_custom_message(self):
        exc = InvalidBodyWeightError("Custom error")
        assert str(exc) == "Custom error"

    def test_message_contains_no_sql(self):
        exc = InvalidBodyWeightError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)
        assert "FROM" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = InvalidBodyWeightError()
        assert "postgresql" not in str(exc).lower()
        assert "localhost" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = InvalidBodyWeightError()
        assert "password" not in str(exc).lower()
        assert "jwt" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = InvalidBodyWeightError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_repr_contains_no_secrets(self):
        exc = InvalidBodyWeightError()
        assert "secret" not in repr(exc).lower()

    def test_can_be_caught_as_base(self):
        with pytest.raises(BodyWeightError):
            raise InvalidBodyWeightError()

    def test_args_behavior(self):
        exc = InvalidBodyWeightError()
        assert exc.args == ("The body-weight entry contains invalid data.",)

    def test_custom_args_behavior(self):
        exc = InvalidBodyWeightError("custom")
        assert exc.args == ("custom",)

    def test_no_env_access(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "environ" not in source

    def test_no_network_access(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "http" not in source.lower()

    def test_hashable(self):
        exc = InvalidBodyWeightError()
        d = {exc: "mapped"}
        assert d[exc] == "mapped"


class TestDuplicateBodyWeightDateError:
    def test_inherits_from_body_weight_error(self):
        assert issubclass(DuplicateBodyWeightDateError, BodyWeightError)

    def test_default_message_stable(self):
        exc = DuplicateBodyWeightDateError()
        assert str(exc) == "A body-weight entry already exists for the selected date."

    def test_custom_message(self):
        exc = DuplicateBodyWeightDateError("Custom duplicate error")
        assert str(exc) == "Custom duplicate error"

    def test_message_contains_no_sql(self):
        exc = DuplicateBodyWeightDateError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)
        assert "FROM" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = DuplicateBodyWeightDateError()
        assert "postgresql" not in str(exc).lower()
        assert "localhost" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = DuplicateBodyWeightDateError()
        assert "password" not in str(exc).lower()
        assert "jwt" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = DuplicateBodyWeightDateError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_repr_contains_no_secrets(self):
        exc = DuplicateBodyWeightDateError()
        assert "secret" not in repr(exc).lower()

    def test_can_be_raised(self):
        with pytest.raises(DuplicateBodyWeightDateError):
            raise DuplicateBodyWeightDateError()

    def test_can_be_caught_as_base(self):
        with pytest.raises(BodyWeightError):
            raise DuplicateBodyWeightDateError()

    def test_args_behavior(self):
        exc = DuplicateBodyWeightDateError()
        assert exc.args == ("A body-weight entry already exists for the selected date.",)

    def test_custom_args_behavior(self):
        exc = DuplicateBodyWeightDateError("custom")
        assert exc.args == ("custom",)


class TestImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        import app.core.body_weight_exceptions as mod

        assert mod is not None

    def test_import_does_not_require_fastapi(self):
        import app.core.body_weight_exceptions as mod

        assert hasattr(mod, "BodyWeightError")
        assert hasattr(mod, "InvalidBodyWeightError")
        assert hasattr(mod, "DuplicateBodyWeightDateError")

    def test_exceptions_are_hashable(self):
        exc = InvalidBodyWeightError()
        d = {exc: "mapped"}
        assert d[exc] == "mapped"

    def test_module_has_no_star_imports(self):
        import app.core.body_weight_exceptions as mod

        source = open(mod.__file__).read()
        assert "from " in source
