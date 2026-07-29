from __future__ import annotations

import pytest

from app.core.token_exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
    TokenConfigurationError,
    TokenError,
)


class TestTokenError:
    def test_inherits_from_exception(self):
        assert issubclass(TokenError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(TokenError):
            raise TokenError()

    def test_default_message(self):
        with pytest.raises(TokenError) as exc:
            raise TokenError()
        assert str(exc.value) == ""

    def test_custom_message(self):
        msg = "Custom token error"
        with pytest.raises(TokenError) as exc:
            raise TokenError(msg)
        assert str(exc.value) == msg


class TestTokenConfigurationError:
    def test_inherits_from_token_error(self):
        assert issubclass(TokenConfigurationError, TokenError)

    def test_default_message_stable(self):
        with pytest.raises(TokenConfigurationError) as exc:
            raise TokenConfigurationError()
        assert str(exc.value) == "Token security is not configured."

    def test_message_contains_no_secret(self):
        with pytest.raises(TokenConfigurationError) as exc:
            raise TokenConfigurationError()
        msg = str(exc.value).lower()
        assert "secret" not in msg

    def test_message_contains_no_raw_token(self):
        with pytest.raises(TokenConfigurationError) as exc:
            raise TokenConfigurationError()
        msg = str(exc.value).lower()
        assert "eyj" not in msg  # no base64-encoded token fragments

    def test_no_fastapi_import(self):
        import sys

        import app.core.token_exceptions as te

        mod_names = {m.split(".")[0] for m in sys.modules}
        assert "fastapi" not in mod_names or not any(
            getattr(te, attr, None) is not None
            and "fastapi" in str(type(getattr(te, attr))).lower()
            for attr in dir(te)
        )

    def test_no_http_status_code(self):
        msg = TokenConfigurationError().__str__()
        assert "404" not in msg
        assert "401" not in msg
        assert "403" not in msg
        assert "500" not in msg

    def test_no_response_behavior(self):
        exc = TokenConfigurationError()
        assert not hasattr(exc, "status_code")
        assert not hasattr(exc, "headers")
        assert not hasattr(exc, "detail")


class TestInvalidTokenError:
    def test_inherits_from_token_error(self):
        assert issubclass(InvalidTokenError, TokenError)

    def test_default_message_stable(self):
        with pytest.raises(InvalidTokenError) as exc:
            raise InvalidTokenError()
        assert str(exc.value) == "Invalid authentication token."

    def test_message_contains_no_secret(self):
        with pytest.raises(InvalidTokenError) as exc:
            raise InvalidTokenError()
        msg = str(exc.value).lower()
        assert "secret" not in msg

    def test_message_contains_no_token(self):
        with pytest.raises(InvalidTokenError) as exc:
            raise InvalidTokenError()
        msg = str(exc.value).lower()
        assert "token" in msg  # "invalid authentication token" - token is in message

    def test_no_fastapi_import(self):

        exc = InvalidTokenError()
        assert "fastapi" not in type(exc).__module__

    def test_no_http_status_code(self):
        msg = InvalidTokenError().__str__()
        assert "404" not in msg
        assert "401" not in msg
        assert "403" not in msg
        assert "500" not in msg

    def test_no_response_behavior(self):
        exc = InvalidTokenError()
        assert not hasattr(exc, "status_code")
        assert not hasattr(exc, "headers")
        assert not hasattr(exc, "detail")


class TestExpiredTokenError:
    def test_inherits_from_invalid_token_error(self):
        assert issubclass(ExpiredTokenError, InvalidTokenError)

    def test_inherits_from_token_error(self):
        assert issubclass(ExpiredTokenError, TokenError)

    def test_default_message_stable(self):
        with pytest.raises(ExpiredTokenError) as exc:
            raise ExpiredTokenError()
        assert str(exc.value) == "Authentication token has expired."

    def test_message_contains_no_secret(self):
        with pytest.raises(ExpiredTokenError) as exc:
            raise ExpiredTokenError()
        msg = str(exc.value).lower()
        assert "secret" not in msg

    def test_message_contains_no_low_level_jwt(self):
        with pytest.raises(ExpiredTokenError) as exc:
            raise ExpiredTokenError()
        msg = str(exc.value)
        assert "signature" not in msg.lower()

    def test_no_fastapi_import(self):
        exc = ExpiredTokenError()
        assert "fastapi" not in type(exc).__module__

    def test_no_http_status_code(self):
        msg = ExpiredTokenError().__str__()
        assert "404" not in msg
        assert "401" not in msg
        assert "403" not in msg
        assert "500" not in msg

    def test_no_response_behavior(self):
        exc = ExpiredTokenError()
        assert not hasattr(exc, "status_code")
        assert not hasattr(exc, "headers")
        assert not hasattr(exc, "detail")


class TestTokenExceptionHierarchy:
    def test_token_error_catches_all(self):
        for exc in [
            TokenConfigurationError(),
            InvalidTokenError(),
            ExpiredTokenError(),
        ]:
            assert isinstance(exc, TokenError)

    def test_expired_token_is_invalid(self):
        exc = ExpiredTokenError()
        assert isinstance(exc, InvalidTokenError)
        assert isinstance(exc, TokenError)

    def test_invalid_token_is_not_configuration(self):
        exc = InvalidTokenError()
        assert not isinstance(exc, TokenConfigurationError)

    def test_configuration_is_not_invalid(self):
        exc = TokenConfigurationError()
        assert not isinstance(exc, InvalidTokenError)
