from __future__ import annotations

import pytest

from app.core.config import (
    Settings,
    validate_secret_strength,
)
from app.core.security import hash_password, verify_password

ARGON2_PREFIX = "$argon2id$"


class TestHashPassword:
    def test_returns_non_empty_string(self):
        h = hash_password("my_secure_password")
        assert isinstance(h, str)
        assert len(h) > 0

    def test_argon2_phc_format(self):
        h = hash_password("test_password")
        assert h.startswith(ARGON2_PREFIX)
        parts = h.split("$")
        assert len(parts) == 6
        assert parts[1] == ARGON2_PREFIX.replace("$", "")
        assert parts[2].startswith("v=")

    def test_different_salts(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2

    def test_empty_password_raises(self):
        with pytest.raises(ValueError, match="password must not be empty"):
            hash_password("")

    def test_whitespace_password_does_not_raise(self):
        h = hash_password("   ")
        assert h.startswith(ARGON2_PREFIX)

    def test_unicode_password(self):
        h = hash_password("pässwörd_123_日本語")
        assert h.startswith(ARGON2_PREFIX)

    def test_very_long_password(self):
        pwd = "x" * 1000
        h = hash_password(pwd)
        assert h.startswith(ARGON2_PREFIX)

    def test_special_characters(self):
        h = hash_password("!@#$%^&*()_+-=[]{}|;':\",./<>?")
        assert h.startswith(ARGON2_PREFIX)


class TestVerifyPassword:
    def test_correct_password(self):
        password = "correct_password"
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_incorrect_password(self):
        h = hash_password("real_password")
        assert verify_password("wrong_password", h) is False

    def test_wrong_case(self):
        h = hash_password("Password123")
        assert verify_password("password123", h) is False

    def test_empty_password_against_hash(self):
        h = hash_password("something")
        assert verify_password("", h) is False

    def test_unicode_verification(self):
        password = "Pässwörd_123"
        h = hash_password(password)
        assert verify_password(password, h) is True
        assert verify_password(password.lower(), h) is False

    def test_repeated_verification_stable(self):
        password = "stable_test"
        h = hash_password(password)
        for _ in range(10):
            assert verify_password(password, h) is True
            assert verify_password("wrong", h) is False

    def test_verify_with_empty_hash(self):
        assert verify_password("password", "") is False

    def test_verify_with_invalid_hash_format(self):
        assert verify_password("password", "not_a_valid_hash") is False


class TestHashVerifyRoundTrip:
    def test_multiple_passwords(self):
        passwords = [
            "a",
            "short",
            "a_medium_length_password",
            "A" * 200,
            "!@#$%^&*()",
            "with spaces and 123",
            "email@example.com",
        ]
        for pwd in passwords:
            h = hash_password(pwd)
            assert verify_password(pwd, h) is True
            assert h.startswith(ARGON2_PREFIX)


class TestValidateSecretStrength:
    def test_empty_secret_does_not_raise(self):
        validate_secret_strength("", "TEST_SECRET")

    def test_long_enough_secret_does_not_raise(self):
        validate_secret_strength("a" * 32, "TEST_SECRET")

    def test_short_secret_raises(self):
        with pytest.raises(ValueError, match="TEST_SECRET must be at least 32 characters long"):
            validate_secret_strength("short", "TEST_SECRET")

    def test_exactly_min_length_does_not_raise(self):
        validate_secret_strength("a" * 32, "TEST_SECRET")

    def test_one_less_than_min_length_raises(self):
        with pytest.raises(ValueError):
            validate_secret_strength("a" * 31, "TEST_SECRET")

    def test_custom_min_length(self):
        validate_secret_strength("a" * 16, "TEST_SECRET", min_length=16)

    def test_custom_min_length_failure(self):
        with pytest.raises(ValueError):
            validate_secret_strength("a" * 15, "TEST_SECRET", min_length=16)

    def test_required_empty_raises(self):
        with pytest.raises(ValueError, match="TEST_SECRET must not be empty"):
            validate_secret_strength("", "TEST_SECRET", required=True)


class TestSettingsPasswordHashingSchemes:
    def test_default_scheme(self):
        s = Settings()
        assert s.PASSWORD_HASHING_SCHEMES == "argon2"

    def test_valid_scheme(self):
        s = Settings(PASSWORD_HASHING_SCHEMES="argon2")
        assert s.PASSWORD_HASHING_SCHEMES == "argon2"

    def test_invalid_scheme_raises(self):
        with pytest.raises(ValueError, match="PASSWORD_HASHING_SCHEMES"):
            Settings(PASSWORD_HASHING_SCHEMES="bcrypt")

    def test_empty_scheme_raises(self):
        with pytest.raises(ValueError, match="PASSWORD_HASHING_SCHEMES"):
            Settings(PASSWORD_HASHING_SCHEMES="")


class TestSettingsProductionJwtSecrets:
    def test_development_empty_secrets_ok(self):
        s = Settings(
            APP_ENV="development",
            JWT_SECRET_KEY="",
            REFRESH_TOKEN_SECRET_KEY="",
        )
        assert s.JWT_SECRET_KEY == ""
        assert s.REFRESH_TOKEN_SECRET_KEY == ""

    def test_test_empty_secrets_ok(self):
        s = Settings(
            APP_ENV="test",
            JWT_SECRET_KEY="",
            REFRESH_TOKEN_SECRET_KEY="",
        )
        assert s.JWT_SECRET_KEY == ""
        assert s.REFRESH_TOKEN_SECRET_KEY == ""

    def test_production_empty_jwt_secret_raises(self):
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="",
                REFRESH_TOKEN_SECRET_KEY="a" * 32,
            )

    def test_production_empty_refresh_secret_raises(self):
        with pytest.raises(ValueError, match="REFRESH_TOKEN_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="a" * 32,
                REFRESH_TOKEN_SECRET_KEY="",
            )

    def test_production_short_jwt_secret_raises(self):
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="short",
                REFRESH_TOKEN_SECRET_KEY="a" * 32,
            )

    def test_production_short_refresh_secret_raises(self):
        with pytest.raises(ValueError, match="REFRESH_TOKEN_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="a" * 32,
                REFRESH_TOKEN_SECRET_KEY="short",
            )

    def test_production_valid_secrets_ok(self):
        s = Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="a" * 32,
            REFRESH_TOKEN_SECRET_KEY="b" * 32,
        )
        assert s.JWT_SECRET_KEY == "a" * 32
        assert s.REFRESH_TOKEN_SECRET_KEY == "b" * 32


class TestSecurityModuleAttributes:
    def test_module_has_hash_password(self):
        from app.core import security

        assert hasattr(security, "hash_password")

    def test_module_has_verify_password(self):
        from app.core import security

        assert hasattr(security, "verify_password")

    def test_hash_password_is_callable(self):
        import app.core.security

        assert callable(app.core.security.hash_password)

    def test_verify_password_is_callable(self):
        import app.core.security

        assert callable(app.core.security.verify_password)


class TestRequestIDMiddleware:
    @pytest.mark.asyncio
    async def test_valid_request_id_preserved(self):
        from app.core.middleware import RequestIDMiddleware, get_request_id

        captured_request_id = None

        async def dummy_app(scope, receive, send):
            nonlocal captured_request_id
            captured_request_id = get_request_id()
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"OK"})

        middleware = RequestIDMiddleware(dummy_app)
        sent_messages = []

        async def mock_receive():
            return {"type": "http.request"}

        async def mock_send(message):
            sent_messages.append(message)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", b"valid-request-id-123")],
        }
        await middleware(scope, mock_receive, mock_send)

        assert captured_request_id == "valid-request-id-123"
        start_msg = next(m for m in sent_messages if m["type"] == "http.response.start")
        headers_dict = dict(start_msg["headers"])
        assert headers_dict[b"x-request-id"] == b"valid-request-id-123"

    @pytest.mark.asyncio
    async def test_invalid_request_id_replaced_with_uuid(self):
        from app.core.middleware import RequestIDMiddleware, get_request_id

        captured_request_id = None

        async def dummy_app(scope, receive, send):
            nonlocal captured_request_id
            captured_request_id = get_request_id()
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"OK"})

        middleware = RequestIDMiddleware(dummy_app)
        sent_messages = []

        async def mock_receive():
            return {"type": "http.request"}

        async def mock_send(message):
            sent_messages.append(message)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", b"bad\r\ninjection id with spaces!")],
        }
        await middleware(scope, mock_receive, mock_send)

        assert captured_request_id != "bad\r\ninjection id with spaces!"
        assert len(captured_request_id) == 32
        start_msg = next(m for m in sent_messages if m["type"] == "http.response.start")
        headers_dict = dict(start_msg["headers"])
        assert headers_dict[b"x-request-id"] == captured_request_id.encode("latin-1")

    @pytest.mark.asyncio
    async def test_oversized_request_id_replaced(self):
        from app.core.middleware import RequestIDMiddleware, get_request_id

        captured_request_id = None

        async def dummy_app(scope, receive, send):
            nonlocal captured_request_id
            captured_request_id = get_request_id()
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"OK"})

        middleware = RequestIDMiddleware(dummy_app)
        sent_messages = []

        async def mock_receive():
            return {"type": "http.request"}

        async def mock_send(message):
            sent_messages.append(message)

        scope = {
            "type": "http",
            "headers": [(b"x-request-id", (b"a" * 65))],
        }
        await middleware(scope, mock_receive, mock_send)

        assert len(captured_request_id) == 32

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self):
        from app.core.middleware import RequestIDMiddleware

        called = False

        async def dummy_app(scope, receive, send):
            nonlocal called
            called = True

        middleware = RequestIDMiddleware(dummy_app)
        scope = {"type": "lifespan"}
        await middleware(scope, None, None)
        assert called is True
