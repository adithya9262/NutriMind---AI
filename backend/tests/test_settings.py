import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestAppEnv:
    def test_development_is_valid(self):
        s = Settings(APP_ENV="development")
        assert s.APP_ENV == "development"

    def test_test_is_valid(self):
        s = Settings(APP_ENV="test")
        assert s.APP_ENV == "test"

    def test_production_is_valid(self):
        s = Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="a" * 32,
            REFRESH_TOKEN_SECRET_KEY="b" * 32,
        )
        assert s.APP_ENV == "production"

    def test_invalid_env_raises(self):
        with pytest.raises(ValidationError):
            Settings(APP_ENV="staging")

    def test_empty_env_raises(self):
        with pytest.raises(ValidationError):
            Settings(APP_ENV="")

    def test_whitespace_env_raises(self):
        with pytest.raises(ValidationError):
            Settings(APP_ENV="   ")


class TestApiPrefix:
    def test_valid_prefix(self):
        s = Settings(API_V1_PREFIX="/api/v1")
        assert s.API_V1_PREFIX == "/api/v1"

    def test_trailing_slash_stripped(self):
        s = Settings(API_V1_PREFIX="/api/v1/")
        assert s.API_V1_PREFIX == "/api/v1"

    def test_missing_leading_slash_raises(self):
        with pytest.raises(ValidationError):
            Settings(API_V1_PREFIX="api/v1")

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            Settings(API_V1_PREFIX="")

    def test_slash_only_raises(self):
        with pytest.raises(ValidationError):
            Settings(API_V1_PREFIX="/")

    def test_whitespace_raises(self):
        with pytest.raises(ValidationError):
            Settings(API_V1_PREFIX="  ")


class TestCorsOrigins:
    def test_single_origin(self):
        s = Settings(CORS_ORIGINS="http://localhost:3000")
        assert s.cors_origins_list == ["http://localhost:3000"]

    def test_multiple_origins(self):
        s = Settings(CORS_ORIGINS="http://localhost:3000,http://example.com")
        assert s.cors_origins_list == [
            "http://localhost:3000",
            "http://example.com",
        ]

    def test_whitespace_trimmed(self):
        s = Settings(CORS_ORIGINS=" http://a.com , http://b.com ")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_duplicates_removed(self):
        s = Settings(CORS_ORIGINS="http://a.com,http://a.com")
        assert s.cors_origins_list == ["http://a.com"]

    def test_empty_entries_skipped(self):
        s = Settings(CORS_ORIGINS="http://a.com,,http://b.com")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_all_whitespace_returns_empty(self):
        s = Settings(CORS_ORIGINS="   ,   ")
        assert s.cors_origins_list == []

    def test_empty_string_returns_empty(self):
        s = Settings(CORS_ORIGINS="")
        assert s.cors_origins_list == []


class TestBackendPort:
    def test_default(self):
        s = Settings()
        assert s.BACKEND_PORT == 8000

    def test_port_min(self):
        s = Settings(BACKEND_PORT=1)
        assert s.BACKEND_PORT == 1

    def test_port_max(self):
        s = Settings(BACKEND_PORT=65535)
        assert s.BACKEND_PORT == 65535

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            Settings(BACKEND_PORT=0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            Settings(BACKEND_PORT=-1)

    def test_too_high_raises(self):
        with pytest.raises(ValidationError):
            Settings(BACKEND_PORT=65536)


class TestProductionDebug:
    def test_production_debug_false_allowed(self):
        s = Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="a" * 32,
            REFRESH_TOKEN_SECRET_KEY="b" * 32,
        )
        assert s.DEBUG is False

    def test_production_debug_true_forced_off(self):
        s = Settings(
            APP_ENV="production",
            DEBUG=True,
            JWT_SECRET_KEY="a" * 32,
            REFRESH_TOKEN_SECRET_KEY="b" * 32,
        )
        assert s.DEBUG is False


class TestJwtAlgorithm:
    def test_default_algorithm_is_hs256(self):
        s = Settings()
        assert s.JWT_ALGORITHM == "HS256"

    def test_hs256_accepted(self):
        s = Settings(JWT_ALGORITHM="HS256")
        assert s.JWT_ALGORITHM == "HS256"

    def test_hs384_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ALGORITHM="HS384")

    def test_hs512_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ALGORITHM="HS512")

    def test_rs256_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ALGORITHM="RS256")

    def test_none_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ALGORITHM="none")

    def test_empty_algorithm_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ALGORITHM="")


class TestJwtAccessTokenExpireMinutes:
    def test_default_is_15(self):
        s = Settings(_env_file=None)
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_lifetime_1_accepted(self):
        s = Settings(JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1)
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 1

    def test_lifetime_1440_accepted(self):
        s = Settings(JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440)
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 1440

    def test_lifetime_0_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ACCESS_TOKEN_EXPIRE_MINUTES=0)

    def test_lifetime_1441_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1441)

    def test_negative_lifetime_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ACCESS_TOKEN_EXPIRE_MINUTES=-1)

    def test_non_integer_lifetime_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15.5)


class TestJwtIssuer:
    def test_default_issuer(self):
        s = Settings()
        assert s.JWT_ISSUER == "nutrimind-ai"

    def test_surrounding_whitespace_stripped(self):
        s = Settings(JWT_ISSUER="  nutrimind-ai  ")
        assert s.JWT_ISSUER == "nutrimind-ai"

    def test_blank_issuer_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ISSUER="")

    def test_whitespace_only_issuer_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_ISSUER="   ")

    def test_custom_issuer_accepted(self):
        s = Settings(JWT_ISSUER="custom-issuer")
        assert s.JWT_ISSUER == "custom-issuer"


class TestJwtAudience:
    def test_default_audience(self):
        s = Settings()
        assert s.JWT_AUDIENCE == "nutrimind-ai-api"

    def test_surrounding_whitespace_stripped(self):
        s = Settings(JWT_AUDIENCE="  nutrimind-ai-api  ")
        assert s.JWT_AUDIENCE == "nutrimind-ai-api"

    def test_blank_audience_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_AUDIENCE="")

    def test_whitespace_only_audience_rejected(self):
        with pytest.raises(ValidationError):
            Settings(JWT_AUDIENCE="   ")

    def test_custom_audience_accepted(self):
        s = Settings(JWT_AUDIENCE="custom-audience")
        assert s.JWT_AUDIENCE == "custom-audience"


class TestJwtSecretBehavior:
    def test_development_starts_without_jwt_secret(self):
        s = Settings(APP_ENV="development", JWT_SECRET_KEY="")
        assert s.JWT_SECRET_KEY == ""

    def test_test_starts_without_jwt_secret(self):
        s = Settings(APP_ENV="test", JWT_SECRET_KEY="")
        assert s.JWT_SECRET_KEY == ""

    def test_production_rejects_missing_secret(self):
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="",
                REFRESH_TOKEN_SECRET_KEY="a" * 32,
            )

    def test_production_rejects_empty_secret(self):
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="",
                REFRESH_TOKEN_SECRET_KEY="a" * 32,
            )

    def test_production_rejects_weak_secret(self):
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="short",
                REFRESH_TOKEN_SECRET_KEY="a" * 32,
            )

    def test_production_accepts_strong_secret(self):
        s = Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="a" * 32,
            REFRESH_TOKEN_SECRET_KEY="b" * 32,
        )
        assert s.JWT_SECRET_KEY == "a" * 32

    def test_secret_not_in_validation_message(self):
        with pytest.raises(ValueError) as exc:
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="",
                REFRESH_TOKEN_SECRET_KEY="a" * 32,
            )
        msg = str(exc.value)
        assert "a" * 32 not in msg
        assert "replace_with" not in msg
