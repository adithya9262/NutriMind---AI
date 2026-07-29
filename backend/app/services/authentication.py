from __future__ import annotations

import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_exceptions import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    OAuthAccountExistsError,
)
from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.models.ai_coach import AIUserMemory
from app.models.enums import GoalType
from app.models.goal import Goal
from app.models.nutrition_profile import NutritionProfile
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest

logger = logging.getLogger(__name__)

SUPABASE_PASSWORD_SENTINEL = "$supabase$"


class AuthenticationService:
    def __init__(self, user_repository: UserRepository, settings: Settings | None = None) -> None:
        self._user_repository = user_repository
        self._settings = settings

    async def _verify_password_via_supabase(self, email: str, password: str) -> bool:
        """Verify password against Supabase for users with sentinel hash."""
        if self._settings is None or not self._settings.SUPABASE_URL or not self._settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("Supabase credentials not configured, cannot verify password")
            return False

        url = f"{self._settings.SUPABASE_URL.rstrip('/')}/auth/v1/verify"
        headers = {
            "apikey": self._settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {self._settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "email": email,
            "password": password,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers, json=data)
                return resp.status_code == 200
        except httpx.RequestError as e:
            logger.error(f"Supabase password verification failed: {e}")
            return False

    async def _initialize_user_resources(self, user_id: uuid.UUID) -> None:
        session: AsyncSession = self._user_repository._session

        # Check if initialized
        stmt = select(NutritionProfile).where(NutritionProfile.user_id == user_id)
        existing = await session.execute(stmt)
        if existing.scalars().first():
            return

        profile = NutritionProfile(user_id=user_id)
        goal = Goal(
            user_id=user_id,
            goal_type=GoalType.MAINTAIN_WEIGHT,
            title="General Health & Maintenance",
            description="Default goal to maintain a healthy lifestyle.",
        )
        memory = AIUserMemory(
            user_id=user_id,
            memory_type="onboarding",
            content="User just created their account.",
            importance_score=1.0,
            confidence=1.0,
        )
        session.add(profile)
        session.add(goal)
        session.add(memory)
        await session.flush()

    async def register(self, request: RegisterRequest) -> User:
        email = str(request.email)
        existing = await self._user_repository.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyRegisteredError()
        password_hash = hash_password(request.password)
        user = await self._user_repository.create(
            email=email,
            password_hash=password_hash,
        )
        await self._initialize_user_resources(user.id)
        return user

    async def authenticate(self, request: LoginRequest) -> User:
        email = str(request.email)
        user = await self._user_repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError()
        if user.password_hash == SUPABASE_PASSWORD_SENTINEL:
            # User has sentinel hash - verify against Supabase
            if await self._verify_password_via_supabase(email, request.password):
                # Password verified via Supabase - update local hash and allow login
                new_hash = hash_password(request.password)
                await self._user_repository.update_password(user.id, new_hash)
                logger.info(f"Synced password hash for user {user.id} after Supabase verification")
            else:
                raise OAuthAccountExistsError()
        else:
            if not verify_password(request.password, user.password_hash):
                raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveAccountError()
        return user


    async def sync_supabase_user(
        self,
        supabase_email: str,
        supabase_user_id: str,
    ) -> User:
        email = supabase_email.strip().lower()
        existing = await self._user_repository.get_by_email(email)
        if existing is not None:
            return existing

        try:
            uid = uuid.UUID(supabase_user_id)
        except ValueError:
            uid = uuid.uuid4()

        user = await self._user_repository.create(
            email=email,
            password_hash=SUPABASE_PASSWORD_SENTINEL,
            user_id=uid,
        )
        await self._initialize_user_resources(user.id)
        return user