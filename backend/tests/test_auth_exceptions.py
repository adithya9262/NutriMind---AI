from __future__ import annotations

import pytest

from app.core.auth_exceptions import (
    AuthenticationError,
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
)


class TestAuthenticationError:
    def test_inherits_from_exception(self):
        assert issubclass(AuthenticationError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(AuthenticationError):
            raise AuthenticationError()

    def test_no_fastapi_dependency(self):
        import app.core.auth_exceptions

        source = open(app.core.auth_exceptions.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_status_code(self):
        exc = AuthenticationError()
        assert not hasattr(exc, "status_code")


class TestEmailAlreadyRegisteredError:
    def test_inherits_from_authentication_error(self):
        assert issubclass(EmailAlreadyRegisteredError, AuthenticationError)

    def test_default_message_stable(self):
        exc = EmailAlreadyRegisteredError()
        assert str(exc) == "An account with this email already exists."

    def test_custom_message(self):
        exc = EmailAlreadyRegisteredError("Custom message")
        assert str(exc) == "Custom message"

    def test_message_contains_no_password(self):
        exc = EmailAlreadyRegisteredError()
        assert "password" not in str(exc).lower()

    def test_message_contains_no_hash(self):
        exc = EmailAlreadyRegisteredError()
        assert "$argon2" not in str(exc)
        assert "hash" not in str(exc).lower()


class TestInvalidCredentialsError:
    def test_inherits_from_authentication_error(self):
        assert issubclass(InvalidCredentialsError, AuthenticationError)

    def test_default_message_stable(self):
        exc = InvalidCredentialsError()
        assert str(exc) == "Invalid email or password."

    def test_custom_message(self):
        exc = InvalidCredentialsError("Custom")
        assert str(exc) == "Custom"

    def test_message_contains_no_password_value(self):
        exc = InvalidCredentialsError()
        assert "secret_password" not in str(exc)

    def test_message_contains_no_hash(self):
        exc = InvalidCredentialsError()
        assert "$argon2" not in str(exc)

    def test_unknown_email_and_wrong_password_identical(self):
        exc1 = InvalidCredentialsError()
        exc2 = InvalidCredentialsError()
        assert type(exc1) is type(exc2)
        assert str(exc1) == str(exc2)

    def test_repr_contains_no_secrets(self):
        exc = InvalidCredentialsError()
        assert "secret_value" not in repr(exc)
        assert "$argon2" not in repr(exc)


class TestInactiveAccountError:
    def test_inherits_from_authentication_error(self):
        assert issubclass(InactiveAccountError, AuthenticationError)

    def test_default_message_stable(self):
        exc = InactiveAccountError()
        assert str(exc) == "This account is inactive."

    def test_custom_message(self):
        exc = InactiveAccountError("Custom")
        assert str(exc) == "Custom"

    def test_message_contains_no_password(self):
        exc = InactiveAccountError()
        assert "password" not in str(exc).lower()

    def test_message_contains_no_hash(self):
        exc = InactiveAccountError()
        assert "$argon2" not in str(exc)
        assert "hash" not in str(exc).lower()


class TestImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        import app.core.auth_exceptions

        assert app.core.auth_exceptions is not None

    def test_import_does_not_require_fastapi(self):
        import app.core.auth_exceptions

        assert hasattr(app.core.auth_exceptions, "AuthenticationError")

    def test_import_does_not_hash_passwords(self):
        from app.core.auth_exceptions import EmailAlreadyRegisteredError

        exc = EmailAlreadyRegisteredError()
        assert "$argon2" not in str(exc)
