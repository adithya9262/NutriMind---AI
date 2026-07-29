from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.token_exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
    TokenConfigurationError,
)
from app.core.tokens import AccessTokenClaims, create_access_token, decode_access_token

_A_VALID_SECRET = "a" * 32
_ANOTHER_SECRET = "b" * 32

_TEST_SETTINGS = Settings(
    JWT_SECRET_KEY=_A_VALID_SECRET,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
    REFRESH_TOKEN_SECRET_KEY="c" * 32,
    _env_file=None,
)

_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
_USER_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(secret: str = _A_VALID_SECRET) -> Settings:
    return Settings(
        JWT_SECRET_KEY=secret,
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_SECRET_KEY="c" * 32,
        _env_file=None,
    )


# ===================================================================
# AccessTokenClaims
# ===================================================================


class TestAccessTokenClaimsValid:
    def test_valid_claims_accepted(self):
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=_NOW + timedelta(minutes=15),
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.sub == _USER_ID
        assert claims.type == "access"

    def test_uuid_subject_retained(self):
        uid = uuid.uuid4()
        claims = AccessTokenClaims(
            sub=uid,
            type="access",
            iat=_NOW,
            exp=_NOW + timedelta(minutes=15),
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.sub == uid

    def test_token_type_access_accepted(self):
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=_NOW + timedelta(minutes=15),
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.type == "access"

    def test_iat_retained(self):
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=_NOW + timedelta(minutes=15),
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.iat == _NOW

    def test_exp_retained(self):
        exp = _NOW + timedelta(hours=1)
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=exp,
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.exp == exp

    def test_timezone_aware_iat_accepted(self):
        iat = datetime(2026, 1, 1, tzinfo=UTC)
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=iat,
            exp=iat + timedelta(minutes=15),
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.iat == iat

    def test_timezone_aware_exp_accepted(self):
        exp = datetime(2026, 6, 15, 12, 15, 0, tzinfo=UTC)
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=exp,
            iss="nutrimind-ai",
            aud="nutrimind-ai-api",
        )
        assert claims.exp == exp

    def test_issuer_retained(self):
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=_NOW + timedelta(minutes=15),
            iss="custom-issuer",
            aud="nutrimind-ai-api",
        )
        assert claims.iss == "custom-issuer"

    def test_audience_retained(self):
        claims = AccessTokenClaims(
            sub=_USER_ID,
            type="access",
            iat=_NOW,
            exp=_NOW + timedelta(minutes=15),
            iss="nutrimind-ai",
            aud="custom-audience",
        )
        assert claims.aud == "custom-audience"


class TestAccessTokenClaimsInvalid:
    def test_wrong_token_type_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="refresh",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
            )

    def test_missing_token_type_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
            )

    def test_naive_iat_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=datetime(2026, 6, 15, 12, 0, 0),
                exp=datetime(2026, 6, 15, 12, 15, 0, tzinfo=UTC),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
            )

    def test_naive_exp_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=datetime(2026, 6, 15, 12, 15, 0),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
            )

    def test_exp_equal_to_iat_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW,
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
            )

    def test_exp_earlier_than_iat_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW - timedelta(minutes=1),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
            )

    def test_empty_issuer_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="",
                aud="nutrimind-ai-api",
            )

    def test_whitespace_only_issuer_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="   ",
                aud="nutrimind-ai-api",
            )

    def test_empty_audience_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="",
            )

    def test_whitespace_only_audience_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="   ",
            )

    def test_unexpected_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                unexpected="value",
            )

    def test_email_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                email="test@example.com",
            )

    def test_password_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                password="secret",
            )

    def test_password_hash_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                password_hash="abc",
            )

    def test_role_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                role="admin",
            )

    def test_permissions_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                permissions=["read"],
            )

    def test_nutrition_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                calories=2000,
            )

    def test_refresh_token_claim_rejected(self):
        with pytest.raises(ValidationError):
            AccessTokenClaims(
                sub=_USER_ID,
                type="access",
                iat=_NOW,
                exp=_NOW + timedelta(minutes=15),
                iss="nutrimind-ai",
                aud="nutrimind-ai-api",
                refresh_token="some_token",
            )


# ===================================================================
# create_access_token
# ===================================================================


class TestCreateAccessTokenValid:
    def test_returns_non_empty_string(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_produces_three_jwt_segments(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        assert token.count(".") == 2

    def test_uses_hs256(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_uses_configured_issuer(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert payload["iss"] == "nutrimind-ai"

    def test_uses_configured_audience(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert payload["aud"] == "nutrimind-ai-api"

    def test_includes_subject(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert payload["sub"] == str(_USER_ID)

    def test_subject_is_uuid_string(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        uuid.UUID(payload["sub"])

    def test_includes_type_access(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert payload["type"] == "access"

    def test_includes_iat(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "iat" in payload

    def test_includes_exp(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "exp" in payload

    def test_expiration_equals_configured_lifetime(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        exp_dt = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp_dt == _NOW + timedelta(minutes=15)

    def test_default_lifetime_is_15_minutes(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        exp_dt = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp_dt == _NOW + timedelta(minutes=15)

    def test_custom_valid_lifetime_works(self):
        custom_settings = Settings(
            JWT_SECRET_KEY=_A_VALID_SECRET,
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        token = create_access_token(user_id=_USER_ID, settings=custom_settings, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        exp_dt = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp_dt == _NOW + timedelta(minutes=30)

    def test_uses_timezone_aware_utc(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        iat_dt = datetime.fromtimestamp(payload["iat"], tz=UTC)
        assert iat_dt.tzinfo is not None
        assert str(iat_dt.tzinfo) == "UTC"

    def test_different_user_ids_produce_different_subjects(self):
        uid1 = uuid.uuid4()
        uid2 = uuid.uuid4()
        token1 = create_access_token(user_id=uid1, settings=_TEST_SETTINGS, now=_NOW)
        token2 = create_access_token(user_id=uid2, settings=_TEST_SETTINGS, now=_NOW)
        p1 = pyjwt.decode(
            token1,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        p2 = pyjwt.decode(
            token2,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert p1["sub"] != p2["sub"]

    def test_deterministic_explicit_now_works(self):
        uid = uuid.uuid4()
        token1 = create_access_token(user_id=uid, settings=_TEST_SETTINGS, now=_NOW)
        token2 = create_access_token(user_id=uid, settings=_TEST_SETTINGS, now=_NOW)
        assert token1 == token2

    def test_token_contains_no_email(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "email" not in payload

    def test_token_contains_no_password(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "password" not in payload

    def test_token_contains_no_password_hash(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "password_hash" not in payload

    def test_token_contains_no_role(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "role" not in payload

    def test_token_contains_no_permissions(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "permissions" not in payload

    def test_token_contains_no_nutrition_data(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        for key in ("calories", "protein", "carbs", "fat", "bmi", "bmr", "tdee"):
            assert key not in payload

    def test_no_database_query(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        assert token is not None

    def test_no_refresh_token_generated(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        payload = pyjwt.decode(
            token,
            _A_VALID_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False, "verify_aud": False},
        )
        assert "refresh_token" not in payload
        assert "refresh" not in payload.get("type", "")


class TestCreateAccessTokenInvalid:
    def test_naive_now_rejected(self):
        naive_now = datetime(2026, 6, 15, 12, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=naive_now)

    def test_missing_secret_raises_token_configuration_error(self):
        no_secret = Settings(
            JWT_SECRET_KEY="",
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(TokenConfigurationError):
            create_access_token(user_id=_USER_ID, settings=no_secret, now=_NOW)

    def test_empty_secret_raises_token_configuration_error(self):
        empty_secret = _settings("")
        with pytest.raises(TokenConfigurationError):
            create_access_token(user_id=_USER_ID, settings=empty_secret, now=_NOW)

    def test_weak_secret_raises_token_configuration_error(self):
        weak_secret = _settings("short")
        with pytest.raises(TokenConfigurationError):
            create_access_token(user_id=_USER_ID, settings=weak_secret, now=_NOW)

    def test_secret_not_in_exception(self):
        no_secret = Settings(
            JWT_SECRET_KEY="",
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(TokenConfigurationError) as exc:
            create_access_token(user_id=_USER_ID, settings=no_secret, now=_NOW)
        assert _A_VALID_SECRET not in str(exc.value)


class TestCreateAccessTokenBoundary:
    def test_no_user_mutation(self):
        uid = uuid.uuid4()
        original = uid
        create_access_token(user_id=uid, settings=_TEST_SETTINGS, now=_NOW)
        assert uid == original

    def test_no_token_pair_created(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        from app.schemas.auth import TokenPair

        assert not isinstance(token, TokenPair)

    def test_no_auth_response_created(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        from app.schemas.auth import AuthResponse

        assert not isinstance(token, AuthResponse)


# ===================================================================
# decode_access_token
# ===================================================================


class TestDecodeAccessTokenValid:
    def test_valid_token_returns_access_token_claims(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert isinstance(claims, AccessTokenClaims)
        assert claims.sub == _USER_ID

    def test_subject_returns_as_uuid(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert isinstance(claims.sub, uuid.UUID)
        assert claims.sub == _USER_ID

    def test_type_returns_access(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.type == "access"

    def test_issuer_validated(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.iss == "nutrimind-ai"

    def test_audience_validated(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.aud == "nutrimind-ai-api"

    def test_iat_retained(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.iat == _NOW

    def test_exp_retained(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.exp == _NOW + timedelta(minutes=15)

    def test_deterministic_explicit_now(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert isinstance(claims, AccessTokenClaims)

    def test_token_accepted_when_exp_after_now(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(
            token, settings=_TEST_SETTINGS, now=_NOW + timedelta(minutes=14)
        )
        assert isinstance(claims, AccessTokenClaims)


class TestDecodeAccessTokenInvalidInput:
    def test_empty_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("", settings=_TEST_SETTINGS, now=_NOW)

    def test_whitespace_only_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("   ", settings=_TEST_SETTINGS, now=_NOW)

    def test_malformed_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("not-a-jwt", settings=_TEST_SETTINGS, now=_NOW)

    def test_one_segment_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("onlyheader", settings=_TEST_SETTINGS, now=_NOW)

    def test_two_segment_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("header.payload", settings=_TEST_SETTINGS, now=_NOW)

    def test_random_text_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_access_token("abc.def.ghi", settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenSignature:
    def test_altered_signature_rejected(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        parts = token.split(".")
        malformed = f"{parts[0]}.{parts[1]}.altered"
        with pytest.raises(InvalidTokenError):
            decode_access_token(malformed, settings=_TEST_SETTINGS, now=_NOW)

    def test_different_secret_rejected(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        diff_settings = Settings(
            JWT_SECRET_KEY=_ANOTHER_SECRET,
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=diff_settings, now=_NOW)

    def test_wrong_configured_secret_rejected(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        wrong_settings = Settings(
            JWT_SECRET_KEY="d" * 32,
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=wrong_settings, now=_NOW)

    def test_invalid_signature_maps_to_invalid_token_error(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.tampered"
        with pytest.raises(InvalidTokenError):
            decode_access_token(tampered, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenAlgorithm:
    _HS384_TEST_SECRET = "a" * 48

    def test_hs384_token_rejected(self):
        token = pyjwt.encode(
            {
                "sub": str(_USER_ID),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            self._HS384_TEST_SECRET,
            algorithm="HS384",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    _HS512_TEST_SECRET = "a" * 64

    def test_hs512_token_rejected(self):
        token = pyjwt.encode(
            {
                "sub": str(_USER_ID),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            self._HS512_TEST_SECRET,
            algorithm="HS512",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_alg_none_token_rejected(self):
        token = pyjwt.encode(
            {
                "sub": str(_USER_ID),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            "",
            algorithm="none",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_algorithm_from_settings_not_from_header(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.sub == token_uid


class TestDecodeAccessTokenExpiration:
    def test_expired_token_raises_expired_token_error(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        with pytest.raises(ExpiredTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW + timedelta(minutes=16))

    def test_exp_exactly_at_now_rejected(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        with pytest.raises(ExpiredTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW + timedelta(minutes=15))

    def test_exp_after_now_accepted(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(
            token, settings=_TEST_SETTINGS, now=_NOW + timedelta(minutes=14, seconds=59)
        )
        assert isinstance(claims, AccessTokenClaims)

    def test_missing_exp_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_invalid_exp_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": "invalid",
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_expired_exception_contains_no_raw_token(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        with pytest.raises(ExpiredTokenError) as exc:
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW + timedelta(hours=1))
        assert token not in str(exc.value)


class TestDecodeAccessTokenIssuedAt:
    def test_future_iat_rejected(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        with pytest.raises(InvalidTokenError, match="issued in the future"):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW - timedelta(seconds=1))

    def test_iat_equal_to_now_accepted(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.iat == _NOW

    def test_past_iat_accepted(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(
            token, settings=_TEST_SETTINGS, now=_NOW + timedelta(minutes=5)
        )
        assert claims.iat == _NOW

    def test_missing_iat_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_invalid_iat_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": "invalid",
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenIssuer:
    def test_wrong_issuer_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "wrong-issuer",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_missing_issuer_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_empty_issuer_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenAudience:
    def test_wrong_audience_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "wrong-audience",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_missing_audience_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_empty_audience_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenSubject:
    def test_missing_subject_rejected(self):
        token = pyjwt.encode(
            {
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_empty_subject_rejected(self):
        token = pyjwt.encode(
            {
                "sub": "",
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_malformed_uuid_subject_rejected(self):
        token = pyjwt.encode(
            {
                "sub": "not-a-uuid",
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenType:
    def test_missing_type_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_refresh_type_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "refresh",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_arbitrary_type_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "bearer",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenExtraClaims:
    def test_email_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "email": "test@example.com",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_password_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "password": "secret",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_password_hash_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "password_hash": "abc",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_role_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "role": "admin",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_permissions_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "permissions": ["read"],
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_nutrition_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "calories": 2000,
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)

    def test_unknown_claim_rejected(self):
        token_uid = uuid.uuid4()
        token = pyjwt.encode(
            {
                "sub": str(token_uid),
                "type": "access",
                "iat": _NOW,
                "exp": _NOW + timedelta(minutes=15),
                "iss": "nutrimind-ai",
                "aud": "nutrimind-ai-api",
                "unknown_key": "value",
            },
            _A_VALID_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)


class TestDecodeAccessTokenConfiguration:
    def test_missing_secret_raises_token_configuration_error(self):
        no_secret = Settings(
            JWT_SECRET_KEY="",
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(TokenConfigurationError):
            decode_access_token("abc.def.ghi", settings=no_secret, now=_NOW)

    def test_weak_secret_raises_token_configuration_error(self):
        weak_secret = Settings(
            JWT_SECRET_KEY="short",
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(TokenConfigurationError):
            decode_access_token("abc.def.ghi", settings=weak_secret, now=_NOW)

    def test_secret_absent_from_exception(self):
        no_secret = Settings(
            JWT_SECRET_KEY="",
            REFRESH_TOKEN_SECRET_KEY="c" * 32,
        )
        with pytest.raises(TokenConfigurationError) as exc:
            decode_access_token("abc.def.ghi", settings=no_secret, now=_NOW)
        assert _A_VALID_SECRET not in str(exc.value)


class TestDecodeAccessTokenSecurity:
    def test_raw_token_absent_from_exceptions(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        parts = token.split(".")
        malformed = f"{parts[0]}.{parts[1]}.bad"
        with pytest.raises((InvalidTokenError, TokenConfigurationError)) as exc:
            decode_access_token(malformed, settings=_TEST_SETTINGS, now=_NOW)
        assert malformed not in str(exc.value)

    def test_low_level_jwt_exception_not_exposed(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        parts = token.split(".")
        malformed = f"{parts[0]}.{parts[1]}.tampered"
        with pytest.raises(InvalidTokenError) as exc:
            decode_access_token(malformed, settings=_TEST_SETTINGS, now=_NOW)
        msg = str(exc.value)
        assert "signature" not in msg.lower()

    def test_no_database_query(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert isinstance(claims, AccessTokenClaims)

    def test_no_user_lookup(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert claims.sub == _USER_ID

    def test_no_is_active_check(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert not hasattr(claims, "is_active")

    def test_no_is_verified_check(self):
        token = create_access_token(user_id=_USER_ID, settings=_TEST_SETTINGS, now=_NOW)
        claims = decode_access_token(token, settings=_TEST_SETTINGS, now=_NOW)
        assert not hasattr(claims, "is_verified")
