from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from pydantic import UUID4, BaseModel, ConfigDict, field_validator, model_validator

from app.core.config import Settings
from app.core.token_exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
    TokenConfigurationError,
)


class AccessTokenClaims(BaseModel):
    sub: UUID4
    type: Literal["access"]
    iat: datetime
    exp: datetime
    iss: str
    aud: str

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("iat", "exp", mode="before")
    @classmethod
    def _ensure_timezone_aware(cls, v: datetime | int | float) -> datetime:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=UTC)
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("Datetime must be timezone-aware")
            return v
        raise ValueError("Invalid datetime value")

    @model_validator(mode="after")
    def _validate_exp_after_iat(self) -> AccessTokenClaims:
        if self.exp <= self.iat:
            raise ValueError("exp must be strictly later than iat")
        return self

    @field_validator("iss", "aud")
    @classmethod
    def _validate_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Value must not be empty or whitespace-only")
        return v


def create_access_token(
    *,
    user_id: uuid.UUID,
    settings: Settings,
    email: str = "",
    now: datetime | None = None,
) -> str:
    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        raise TokenConfigurationError()

    if now is None:
        now = datetime.now(UTC)
    elif now.tzinfo is None:
        raise ValueError("Explicit now must be timezone-aware")

    iat = now
    exp = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict = {
        "sub": str(user_id),
        "type": "access",
        "iat": iat,
        "exp": exp,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    if email:
        payload["email"] = email

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_access_token(
    token: str,
    *,
    settings: Settings,
    now: datetime | None = None,
) -> AccessTokenClaims:
    if not token or not token.strip():
        raise InvalidTokenError("Token must not be empty")

    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        raise TokenConfigurationError()

    if now is None:
        now = datetime.now(UTC)
    elif now.tzinfo is None:
        raise InvalidTokenError("Explicit now must be timezone-aware")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_exp": False,
                "verify_iat": False,
                "require": ["sub", "iat", "exp", "iss", "aud"],
            },
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError()
    except (
        jwt.InvalidSignatureError,
        jwt.DecodeError,
        jwt.InvalidAlgorithmError,
        jwt.InvalidAudienceError,
        jwt.InvalidIssuerError,
        jwt.MissingRequiredClaimError,
        jwt.ImmatureSignatureError,
        jwt.InvalidIssuedAtError,
    ):
        raise InvalidTokenError()

    exp_ts = payload.get("exp")
    if exp_ts is not None:
        if not isinstance(exp_ts, (int, float)):
            raise InvalidTokenError()
        exp_dt = datetime.fromtimestamp(exp_ts, tz=UTC)
        if exp_dt <= now:
            raise ExpiredTokenError()

    iat_ts = payload.get("iat")
    if iat_ts is not None:
        if not isinstance(iat_ts, (int, float)):
            raise InvalidTokenError()
        iat_dt = datetime.fromtimestamp(iat_ts, tz=UTC)
        if iat_dt > now:
            raise InvalidTokenError("Token issued in the future")

    try:
        return AccessTokenClaims(**payload)
    except Exception:
        raise InvalidTokenError()
