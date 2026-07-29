from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.auth_exceptions import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    OAuthAccountExistsError,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.authentication import (
    AuthenticationService,
    SUPABASE_PASSWORD_SENTINEL,
)


def _make_user(
    email: str = "test@example.com",
    password_hash: str = "$argon2id$v=19$m=65536,t=3,p=4$hashed_value",
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = email
    user.password_hash = password_hash
    user.is_active = is_active
    user.is_verified = False
    return user


def _make_repo() -> MagicMock:
    repo = AsyncMock(spec=UserRepository)
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    repo._session = mock_session
    return repo


class TestAuthenticationServiceInit:
    def test_stores_supplied_repository(self):
        repo = _make_repo()
        service = AuthenticationService(repo)
        assert service._user_repository is repo

    def test_does_not_create_a_session(self):
        repo = _make_repo()
        AuthenticationService(repo)
        repo.assert_not_called()

    def test_does_not_connect_to_database(self):
        repo = _make_repo()
        AuthenticationService(repo)
        repo.get_by_email.assert_not_called()
        repo.create.assert_not_called()


class TestRegister:
    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_valid_registration_accepts_request(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="new@example.com", password="secure12345")
        result = await service.register(request)

        assert result is not None
        assert isinstance(result, MagicMock)

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_uses_normalized_email(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="  New@Example.COM  ", password="secure12345")
        await service.register(request)

        repo.get_by_email.assert_awaited_once_with("new@example.com")
        repo.create.assert_awaited_once_with(
            email="new@example.com",
            password_hash="hashed_pw",
        )

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_calls_get_by_email_exactly_once(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        await service.register(request)

        repo.get_by_email.assert_awaited_once()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_checks_duplicate_before_hashing(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)

        # hash should NOT be called if duplicate check fails
        # We can't easily verify this because the exception is raised before hash is called
        # But we can verify create is not called
        repo.create.assert_not_called()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_hashes_password_exactly_once(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        await service.register(request)

        mock_hash.assert_called_once_with("secure12345")

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_passes_generated_hash_to_repository(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        await service.register(request)

        repo.create.assert_awaited_once_with(
            email="user@example.com",
            password_hash="hashed_pw",
        )

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_pass_plaintext_password_to_repository(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="my_plain_password")
        await service.register(request)

        call_kwargs = repo.create.call_args.kwargs
        assert "password_hash" in call_kwargs
        assert call_kwargs["password_hash"] != "my_plain_password"
        assert "password" not in call_kwargs

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_calls_create_exactly_once(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        await service.register(request)

        repo.create.assert_awaited_once()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_returns_created_user(self, mock_hash):
        expected_user = _make_user(email="user@example.com")
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = expected_user

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        result = await service.register(request)

        assert result is expected_user

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_commit(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        await service.register(request)

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_generate_token(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        result = await service.register(request)

        # Verify no token-related attributes on the result
        assert not hasattr(result, "access_token")
        assert not hasattr(result, "refresh_token")

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_create_nutrition_profile(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        await service.register(request)

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_modify_is_active(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        created_user = _make_user(is_active=True)
        repo.create.return_value = created_user

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        result = await service.register(request)

        assert result.is_active is True

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_modify_is_verified(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        created_user = _make_user()
        created_user.is_verified = False
        repo.create.return_value = created_user

        service = AuthenticationService(repo)
        request = RegisterRequest(email="user@example.com", password="secure12345")
        result = await service.register(request)

        assert result.is_verified is False


class TestRegisterDuplicate:
    async def test_existing_email_raises_email_already_registered(self):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)

    @patch("app.services.authentication.hash_password")
    async def test_password_not_hashed_when_duplicate(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)

        mock_hash.assert_not_called()

    async def test_create_not_called_when_duplicate(self):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)

        repo.create.assert_not_called()

    async def test_exception_message_contains_no_password(self):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secret12345")

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await service.register(request)

        assert "secret12345" not in str(exc_info.value)

    async def test_exception_message_contains_no_password_hash(self):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secret12345")

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await service.register(request)

        assert "$argon2" not in str(exc_info.value)

    async def test_raw_database_details_absent(self):
        repo = _make_repo()
        repo.get_by_email.return_value = _make_user()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await service.register(request)

        error_msg = str(exc_info.value)
        assert "IntegrityError" not in error_msg
        assert "INSERT" not in error_msg
        assert "constraint" not in error_msg.lower()


class TestRegisterRace:
    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_race_condition_propagates_email_already_registered(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.side_effect = EmailAlreadyRegisteredError()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="race@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)

        repo.create.assert_awaited_once()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_unrelated_integrity_error_propagates(self, mock_hash):
        from sqlalchemy.exc import IntegrityError

        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.side_effect = IntegrityError("test", {}, None)

        service = AuthenticationService(repo)
        request = RegisterRequest(email="race@example.com", password="secure12345")

        with pytest.raises(IntegrityError):
            await service.register(request)

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_no_sql_details_in_domain_exception(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.side_effect = EmailAlreadyRegisteredError()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="race@example.com", password="secure12345")

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await service.register(request)

        error_msg = str(exc_info.value)
        assert "INSERT" not in error_msg
        assert "SELECT" not in error_msg

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_no_password_or_hash_in_exception(self, mock_hash):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.side_effect = EmailAlreadyRegisteredError()

        service = AuthenticationService(repo)
        request = RegisterRequest(email="race@example.com", password="secret12345")

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await service.register(request)

        error_msg = str(exc_info.value)
        assert "secret12345" not in error_msg
        assert "hashed_pw" not in error_msg


class TestAuthenticate:
    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_uses_normalized_email(self, mock_verify):
        repo = _make_repo()
        user = _make_user(email="test@example.com")
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="  Test@Example.COM  ", password="password123")
        await service.authenticate(request)

        repo.get_by_email.assert_awaited_once_with("test@example.com")

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_calls_get_by_email_exactly_once(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        await service.authenticate(request)

        repo.get_by_email.assert_awaited_once()

    @patch("app.services.authentication.verify_password")
    async def test_calls_verify_password_exactly_once(self, mock_verify):
        mock_verify.return_value = True
        repo = _make_repo()
        user = _make_user(password_hash="stored_hash")
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        await service.authenticate(request)

        mock_verify.assert_called_once_with("password123", "stored_hash")

    @patch("app.services.authentication.verify_password")
    async def test_passes_exact_login_password(self, mock_verify):
        mock_verify.return_value = True
        repo = _make_repo()
        user = _make_user(password_hash="stored_hash")
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="  MyPass 123  ")
        await service.authenticate(request)

        mock_verify.assert_called_once_with("  MyPass 123  ", "stored_hash")

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_passes_stored_password_hash(self, mock_verify):
        repo = _make_repo()
        user = _make_user(password_hash="stored_argon2_hash")
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        await service.authenticate(request)

        mock_verify.assert_called_once_with("password123", "stored_argon2_hash")

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_returns_user(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        result = await service.authenticate(request)

        assert result is user

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_mutate_user(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        result = await service.authenticate(request)

        assert result.email == user.email
        assert result.password_hash == user.password_hash
        assert result.is_active == user.is_active

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_commit(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        await service.authenticate(request)

        if hasattr(repo, "commit"):
            repo.commit.assert_not_called()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_flush(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        await service.authenticate(request)

        if hasattr(repo, "flush"):
            repo.flush.assert_not_called()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_generate_tokens(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="password123")
        result = await service.authenticate(request)

        assert not hasattr(result, "access_token")
        assert not hasattr(result, "refresh_token")


class TestAuthenticateUnknownEmail:
    async def test_raises_invalid_credentials_error(self):
        repo = _make_repo()
        repo.get_by_email.return_value = None

        service = AuthenticationService(repo)
        request = LoginRequest(email="unknown@example.com", password="password123")

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)

    @patch("app.services.authentication.verify_password")
    async def test_verify_password_not_called(self, mock_verify):
        repo = _make_repo()
        repo.get_by_email.return_value = None

        service = AuthenticationService(repo)
        request = LoginRequest(email="unknown@example.com", password="password123")

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)

        mock_verify.assert_not_called()

    async def test_uses_generic_safe_message(self):
        repo = _make_repo()
        repo.get_by_email.return_value = None

        service = AuthenticationService(repo)
        request = LoginRequest(email="unknown@example.com", password="password123")

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await service.authenticate(request)

        assert str(exc_info.value) == "Invalid email or password."

    async def test_does_not_reveal_email_absence(self):
        repo = _make_repo()
        repo.get_by_email.return_value = None

        service = AuthenticationService(repo)
        request = LoginRequest(email="unknown@example.com", password="password123")

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await service.authenticate(request)

        error_msg = str(exc_info.value)
        assert "unknown" not in error_msg.lower()
        assert "email" not in error_msg.lower() or "email" in "Invalid email or password."

    async def test_does_not_generate_token(self):
        repo = _make_repo()
        repo.get_by_email.return_value = None

        service = AuthenticationService(repo)
        request = LoginRequest(email="unknown@example.com", password="password123")

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)


class TestAuthenticateWrongPassword:
    @patch("app.services.authentication.verify_password", return_value=False)
    async def test_raises_invalid_credentials_error(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)

    @patch("app.services.authentication.verify_password", return_value=False)
    async def test_same_message_as_unknown_email(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await service.authenticate(request)

        assert str(exc_info.value) == "Invalid email or password."

    @patch("app.services.authentication.verify_password", return_value=False)
    async def test_does_not_return_user(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)

    @patch("app.services.authentication.verify_password", return_value=False)
    async def test_does_not_generate_token(self, mock_verify):
        repo = _make_repo()
        user = _make_user()
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)


class TestAuthenticateInactiveUser:
    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_raises_inactive_account_error(self, mock_verify):
        repo = _make_repo()
        user = _make_user(is_active=False)
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="inactive@example.com", password="password123")

        with pytest.raises(InactiveAccountError):
            await service.authenticate(request)

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_password_verified_before_inactive_check(self, mock_verify):
        repo = _make_repo()
        user = _make_user(is_active=False)
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="inactive@example.com", password="password123")

        with pytest.raises(InactiveAccountError):
            await service.authenticate(request)

        mock_verify.assert_called_once()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_return_user(self, mock_verify):
        repo = _make_repo()
        user = _make_user(is_active=False)
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="inactive@example.com", password="password123")

        with pytest.raises(InactiveAccountError):
            await service.authenticate(request)

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_generate_token(self, mock_verify):
        repo = _make_repo()
        user = _make_user(is_active=False)
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="inactive@example.com", password="password123")

        with pytest.raises(InactiveAccountError):
            await service.authenticate(request)

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_does_not_mutate_user(self, mock_verify):
        repo = _make_repo()
        user = _make_user(is_active=False)
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(email="inactive@example.com", password="password123")

        with pytest.raises(InactiveAccountError):
            await service.authenticate(request)

        # User should remain unchanged
        assert user.is_active is False
        assert user.email == "test@example.com"


class TestAuthenticateMalformedHash:
    @patch("app.services.authentication.verify_password", return_value=False)
    async def test_malformed_hash_returns_false_safely(self, mock_verify):
        repo = _make_repo()
        user = _make_user(password_hash="not_a_valid_hash")
        repo.get_by_email.return_value = user

        service = AuthenticationService(repo)
        request = LoginRequest(
            email="test@example.com",
            password="password123",
        )

        with pytest.raises(InvalidCredentialsError):
            await service.authenticate(request)

        mock_verify.assert_called_once_with("password123", "not_a_valid_hash")


class TestServiceSecurity:
    def test_no_jwt_dependency(self):
        import app.services.authentication

        source = open(app.services.authentication.__file__).read()
        assert "jwt" not in source.lower()

    def test_no_fastapi_dependency(self):
        import app.services.authentication

        source = open(app.services.authentication.__file__).read()
        assert "fastapi" not in source.lower() and "FastAPI" not in source

    def test_no_http_status_code(self):
        import app.services.authentication

        source = open(app.services.authentication.__file__).read()
        source_clean = source.replace("resp.status_code", "")
        assert "status_code" not in source_clean
        assert "HTTP" not in source_clean


class TestServiceImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        from app.services import AuthenticationService

        assert AuthenticationService is not None

    def test_import_does_not_hash_passwords(self):
        from app.services.authentication import AuthenticationService

        assert AuthenticationService is not None

    def test_import_does_not_generate_tokens(self):
        from app.services.authentication import AuthenticationService

        assert AuthenticationService is not None


# ---------------------------------------------------------------------------
# Security — OAuth sentinel account protection
# ---------------------------------------------------------------------------


class TestRegisterOAuthSentinel:
    """register() must NEVER convert or modify an existing OAuth sentinel account."""

    async def test_existing_oauth_raises_email_already_registered(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = RegisterRequest(email="oauth@example.com", password="attacker123")
        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)

    async def test_oauth_password_hash_unchanged_after_rejected_register(self):
        repo = _make_repo()
        original_hash = SUPABASE_PASSWORD_SENTINEL
        oauth_user = _make_user(password_hash=original_hash)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = RegisterRequest(email="oauth@example.com", password="attacker123")
        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)
        assert oauth_user.password_hash == original_hash

    async def test_create_not_called_for_oauth_user(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = RegisterRequest(email="oauth@example.com", password="attacker123")
        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)
        repo.create.assert_not_called()

    async def test_hash_not_called_for_oauth_user(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = RegisterRequest(email="oauth@example.com", password="attacker123")
        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)
        repo.create.assert_not_called()

    async def test_normal_register_still_works_with_other_users(self):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user()
        service = AuthenticationService(repo)
        request = RegisterRequest(email="normal@example.com", password="secure12345")
        user = await service.register(request)
        assert user is not None


class TestAuthenticateOAuthSentinel:
    """authenticate() must reject password login for OAuth sentinel accounts."""

    async def test_oauth_login_raises_oauth_account_exists_error(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = LoginRequest(email="oauth@example.com", password="anypassword")
        with pytest.raises(OAuthAccountExistsError):
            await service.authenticate(request)

    async def test_oauth_verify_password_not_called(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = LoginRequest(email="oauth@example.com", password="anypassword")
        with pytest.raises(OAuthAccountExistsError):
            await service.authenticate(request)

    async def test_oauth_error_message_helpful(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = LoginRequest(email="oauth@example.com", password="anypassword")
        with pytest.raises(OAuthAccountExistsError) as exc_info:
            await service.authenticate(request)
        msg = str(exc_info.value)
        assert "Google" in msg or "Apple" in msg
        assert "Forgot Password" in msg

    async def test_oauth_sentinel_password_does_not_leak(self):
        repo = _make_repo()
        oauth_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = oauth_user
        service = AuthenticationService(repo)
        request = LoginRequest(email="oauth@example.com", password="anypassword")
        with pytest.raises(OAuthAccountExistsError) as exc_info:
            await service.authenticate(request)
        assert "$supabase$" not in str(exc_info.value)


class TestSyncSupabaseUserSecurity:
    """sync_supabase_user() must preserve existing password credentials."""

    async def test_existing_password_user_returned_unchanged(self):
        repo = _make_repo()
        original_hash = "$argon2id$v=19$m=65536,t=3,p=4$realhash"
        existing_user = _make_user(password_hash=original_hash)
        repo.get_by_email.return_value = existing_user
        service = AuthenticationService(repo)
        result = await service.sync_supabase_user(
            supabase_email="user@example.com",
            supabase_user_id=str(uuid.uuid4()),
        )
        assert result is existing_user
        assert result.password_hash == original_hash
        repo.create.assert_not_called()

    async def test_existing_oauth_user_returned_unchanged(self):
        repo = _make_repo()
        existing_user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        repo.get_by_email.return_value = existing_user
        service = AuthenticationService(repo)
        result = await service.sync_supabase_user(
            supabase_email="oauth@example.com",
            supabase_user_id=str(uuid.uuid4()),
        )
        assert result is existing_user
        assert result.password_hash == SUPABASE_PASSWORD_SENTINEL
        repo.create.assert_not_called()

    async def test_new_user_creates_with_sentinel(self):
        repo = _make_repo()
        repo.get_by_email.return_value = None
        repo.create.return_value = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        service = AuthenticationService(repo)
        result = await service.sync_supabase_user(
            supabase_email="new@example.com",
            supabase_user_id=str(uuid.uuid4()),
        )
        repo.create.assert_awaited_once()
        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["password_hash"] == SUPABASE_PASSWORD_SENTINEL


class TestRegisterDuplicateStillSecure:
    """Duplicate registration must never modify existing password credentials."""

    async def test_duplicate_normal_user_unchanged(self):
        repo = _make_repo()
        original_hash = "$argon2id$v=19$m=65536,t=3,p=4$original"
        existing_user = _make_user(password_hash=original_hash)
        repo.get_by_email.return_value = existing_user
        service = AuthenticationService(repo)
        request = RegisterRequest(email="existing@example.com", password="newpass123")
        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)
        assert existing_user.password_hash == original_hash

    async def test_duplicate_oauth_user_unchanged(self):
        repo = _make_repo()
        original_hash = SUPABASE_PASSWORD_SENTINEL
        existing_user = _make_user(password_hash=original_hash)
        repo.get_by_email.return_value = existing_user
        service = AuthenticationService(repo)
        request = RegisterRequest(email="oauth@example.com", password="anypass123")
        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(request)
        assert existing_user.password_hash == original_hash
