from __future__ import annotations

import base64
import logging
import uuid

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_cache import get_cached_payload, set_cached_payload
from app.core.config import Settings, get_settings
from app.core.middleware import get_request_id
from app.db.dependencies import get_db_session
from app.models.user import User
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

SUPABASE_PASSWORD_SENTINEL = "$supabase$"

security_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Enter an access token (Supabase or backend-issued).",
)

# In-memory user cache is intentionally disabled.
# Caching User ORM instances across requests causes DetachedInstanceError
# because the underlying session is closed after each request.


def _raise_http(status_code: int, code: str, message: str, request_id: str, *, www_auth: bool = True) -> HTTPException:
    headers: dict[str, str] = {"X-Request-ID": request_id}
    if www_auth:
        headers["WWW-Authenticate"] = "Bearer"
    return HTTPException(
        status_code=status_code,
        headers=headers,
        detail={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            },
        },
    )


async def _verify_via_supabase_api(token_str: str, settings: Settings) -> dict | None:
    cached = get_cached_payload(token_str)
    if cached is not None:
        return cached
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token_str}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                set_cached_payload(token_str, data)
                return data
    except Exception:
        pass
    return None


def _decode_supabase_jwt(token_str: str, settings: Settings) -> dict | None:
    if not settings.SUPABASE_JWT_SECRET:
        return None
    secret_keys = [settings.SUPABASE_JWT_SECRET]
    try:
        decoded = base64.b64decode(settings.SUPABASE_JWT_SECRET)
        secret_keys.append(decoded)
    except (ValueError, base64.binascii.Error):
        pass
    for key in secret_keys:
        try:
            return jwt.decode(
                token_str, key,
                algorithms=["HS256"],
                options={"verify_exp": True, "verify_iat": True, "require": ["sub", "exp"]},
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError:
            raise
        except jwt.InvalidTokenError:
            continue
    return None


def _decode_backend_jwt(token_str: str, settings: Settings) -> dict | None:
    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        return None
    try:
        payload = jwt.decode(
            token_str,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True, "verify_iat": True, "require": ["sub", "exp"]},
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(security_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    request_id = get_request_id() or "-"

    if credentials is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer"):
            raise _raise_http(
                status.HTTP_401_UNAUTHORIZED, "INVALID_ACCESS_TOKEN",
                "The access token is invalid.", request_id,
            )
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED",
            "Authentication is required.", request_id,
        )

    if credentials.scheme.lower() != "bearer":
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED",
            "Authentication is required.", request_id,
        )

    if not credentials.credentials or not credentials.credentials.strip():
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "INVALID_ACCESS_TOKEN",
            "The access token is invalid.", request_id,
        )

    token_str = credentials.credentials
    payload: dict | None = None

    try:
        payload = _decode_supabase_jwt(token_str, settings)
    except jwt.ExpiredSignatureError:
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "ACCESS_TOKEN_EXPIRED",
            "The access token has expired.", request_id,
        )

    if payload is None:
        try:
            payload = _decode_backend_jwt(token_str, settings)
        except jwt.ExpiredSignatureError:
            raise _raise_http(
                status.HTTP_401_UNAUTHORIZED, "ACCESS_TOKEN_EXPIRED",
                "The access token has expired.", request_id,
            )

    if payload is None and settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        supabase_data = await _verify_via_supabase_api(token_str, settings)
        if supabase_data:
            payload = {
                "sub": supabase_data.get("id", ""),
                "email": supabase_data.get("email", ""),
            }

    if payload is None:
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "INVALID_ACCESS_TOKEN",
            "The access token is invalid.", request_id,
        )

    supabase_user_id: str | None = payload.get("sub")
    email: str = (payload.get("email") or "").strip().lower()

    if not supabase_user_id:
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "INVALID_ACCESS_TOKEN",
            "The access token is invalid.", request_id,
        )

    try:
        user_uuid = uuid.UUID(supabase_user_id)
    except ValueError:
        raise _raise_http(
            status.HTTP_401_UNAUTHORIZED, "INVALID_ACCESS_TOKEN",
            "The access token is invalid.", request_id,
        )

    repo = UserRepository(session)

    user = await repo.get_by_id(user_uuid)
    if user is None and email:
        user = await repo.get_by_email(email)

    if user is None:
        if email:
            user = await repo.create(
                email=email,
                password_hash=SUPABASE_PASSWORD_SENTINEL,
                user_id=user_uuid,
            )
            await session.commit()
        else:
            raise _raise_http(
                status.HTTP_401_UNAUTHORIZED, "INVALID_ACCESS_TOKEN",
                "The access token is invalid.", request_id,
            )

    if not user.is_active:
        raise _raise_http(
            status.HTTP_403_FORBIDDEN, "INACTIVE_ACCOUNT",
            "This account is inactive.", request_id, www_auth=False,
        )

    return user
