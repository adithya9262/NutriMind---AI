from __future__ import annotations

import logging

import httpx
import jwt as pyjwt
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.auth_exceptions import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    OAuthAccountExistsError,
)
from app.core.config import Settings, get_settings
from app.core.middleware import get_request_id
from app.core.token_exceptions import TokenConfigurationError
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AccessTokenData,
    AuthSuccessResponse,
    LoginRequest,
    PublicUser,
    RegisterRequest,
)
from app.services.authentication import AuthenticationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

async def verify_supabase_token(access_token: str, settings: Settings) -> dict | None:
    if not settings.SUPABASE_URL:
        return None
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    request_headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, headers=request_headers)
            if resp.status_code == 200:
                return resp.json()
        except httpx.RequestError:
            pass
    return None


class AuthMeResponse(BaseModel):
    success: bool
    message: str
    data: PublicUser


class SupabaseSyncRequest(BaseModel):
    access_token: str


@router.get(
    "/me",
    response_model=AuthMeResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> AuthMeResponse:
    public_user = PublicUser.model_validate(current_user)
    return AuthMeResponse(
        success=True,
        message="Current user retrieved successfully.",
        data=public_user,
    )


@router.post(
    "/supabase-sync",
    response_model=AuthSuccessResponse,
    status_code=status.HTTP_200_OK,
)
async def supabase_sync(
    request: Request,
    body: SupabaseSyncRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"

    token = body.access_token

    supabase_user = await verify_supabase_token(token, settings)
    if supabase_user is None:
        try:
            claims = pyjwt.decode(token, options={"verify_signature": False})
            sub = claims.get("sub", "")
            email = claims.get("email", "")
            if sub and email:
                supabase_user = {"id": sub, "email": email}
        except Exception:
            pass

    if supabase_user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_SUPABASE_TOKEN",
                    "message": "The Supabase access token is invalid or expired.",
                    "request_id": request_id,
                },
            },
        )

    supabase_email = (supabase_user.get("email") or "").strip().lower()
    if not supabase_email:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "MISSING_EMAIL",
                    "message": "No email found in Supabase user data.",
                    "request_id": request_id,
                },
            },
        )

    repo = UserRepository(session)
    auth_service = AuthenticationService(repo)

    try:
        user = await auth_service.sync_supabase_user(
            supabase_email=supabase_email,
            supabase_user_id=supabase_user.get("id", ""),
        )
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DIAG] GOOGLE SYNC: provider=google email={supabase_email} supabase_sub={supabase_user.get('id','')} resolved_backend_id={user.id} resolved_backend_email={user.email} password_hash_prefix={user.password_hash[:12]}")
        print(f"[DIAG] GOOGLE SYNC: provider=google email={supabase_email} supabase_sub={supabase_user.get('id','')} resolved_backend_id={user.id} resolved_backend_email={user.email} password_hash_prefix={user.password_hash[:12]}", flush=True)
    except EmailAlreadyRegisteredError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "EMAIL_ALREADY_REGISTERED",
                    "message": "An account with this email already exists.",
                    "request_id": request_id,
                },
            },
        )

    await session.commit()
    await session.refresh(user)

    public_user = PublicUser.model_validate(user)

    backend_token = create_access_token(
        user_id=user.id,
        settings=settings,
        email=user.email,
    )
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return AuthSuccessResponse(
        success=True,
        message="Supabase user synced successfully.",
        data=AccessTokenData(
            user=public_user,
            access_token=backend_token,
            token_type="bearer",
            expires_in=expires_in,
        ),
    )


@router.post(
    "/register",
    response_model=AuthSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
)
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = UserRepository(session)
    auth_service = AuthenticationService(repo, settings)

    try:
        user = await auth_service.register(body)
    except EmailAlreadyRegisteredError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "EMAIL_ALREADY_REGISTERED",
                    "message": "An account with this email already exists.",
                    "request_id": request_id,
                },
            },
        )

    try:
        access_token = create_access_token(user_id=user.id, settings=settings, email=user.email)
    except TokenConfigurationError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_UNAVAILABLE",
                    "message": "Authentication is temporarily unavailable.",
                    "request_id": request_id,
                },
            },
        )

    await session.commit()
    await session.refresh(user)

    public_user = PublicUser.model_validate(user)
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return AuthSuccessResponse(
        success=True,
        message="Registration successful.",
        data=AccessTokenData(
            user=public_user,
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        ),
    )


@router.post(
    "/login",
    response_model=AuthSuccessResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
)
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = UserRepository(session)
    auth_service = AuthenticationService(repo, settings)

    try:
        user = await auth_service.authenticate(body)
    except InvalidCredentialsError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "request_id": request_id,
                },
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except OAuthAccountExistsError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error": {
                    "code": "OAUTH_ACCOUNT_EXISTS",
                    "message": "This account was created with Google or Apple. Please sign in with Google or Apple, or use 'Forgot Password' to set a password.",
                    "request_id": request_id,
                },
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveAccountError:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "error": {
                    "code": "INACTIVE_ACCOUNT",
                    "message": "This account is inactive.",
                    "request_id": request_id,
                },
            },
        )

    try:
        access_token = create_access_token(user_id=user.id, settings=settings, email=user.email)
    except TokenConfigurationError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_UNAVAILABLE",
                    "message": "Authentication is temporarily unavailable.",
                    "request_id": request_id,
                },
            },
        )

    public_user = PublicUser.model_validate(user)
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return AuthSuccessResponse(
        success=True,
        message="Login successful.",
        data=AccessTokenData(
            user=public_user,
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        ),
    )


@router.get(
    "/diag/last-sync",
    response_model=dict,
    include_in_schema=False,
)
async def diag_last_sync() -> dict:
    """Temporary diagnostic endpoint - remove after investigation."""
    return {
        "message": "Call /auth/supabase-sync from frontend to trigger sync logging"
    }
