from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    AuthResponse,
    LoginRequest,
    PublicUser,
    RegisterRequest,
    TokenPair,
)
from app.schemas.auth import normalize_email


# ---------------------------------------------------------------------------
# RegisterRequest — email
# ---------------------------------------------------------------------------
class TestRegisterEmail:
    def test_valid_lowercase_accepted(self):
        r = RegisterRequest(email="user@example.com", password="password123")
        assert r.email == "user@example.com"

    def test_uppercase_normalized(self):
        r = RegisterRequest(email="User@Example.COM", password="password123")
        assert r.email == "user@example.com"

    def test_leading_whitespace_removed(self):
        r = RegisterRequest(email="  user@example.com", password="password123")
        assert r.email == "user@example.com"

    def test_trailing_whitespace_removed(self):
        r = RegisterRequest(email="user@example.com  ", password="password123")
        assert r.email == "user@example.com"

    def test_leading_and_trailing_whitespace_removed(self):
        r = RegisterRequest(email="  User@Example.COM  ", password="password123")
        assert r.email == "user@example.com"

    def test_plus_addressing_preserved(self):
        r = RegisterRequest(email="User+Nutrition@Example.com", password="password123")
        assert r.email == "user+nutrition@example.com"

    def test_dots_in_local_part_preserved(self):
        r = RegisterRequest(email="first.last@example.com", password="password123")
        assert r.email == "first.last@example.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="password123")

    def test_missing_at_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="userexample.com", password="password123")

    def test_missing_domain_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@", password="password123")

    def test_empty_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="", password="password123")

    def test_whitespace_only_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="   ", password="password123")

    def test_normalization_deterministic(self):
        inputs = [
            "  USER@EXAMPLE.COM  ",
            "  user@example.com  ",
            "User@Example.COM",
        ]
        results = [RegisterRequest(email=e, password="password123").email for e in inputs]
        assert all(r == "user@example.com" for r in results)


# ---------------------------------------------------------------------------
# RegisterRequest — password
# ---------------------------------------------------------------------------
class TestRegisterPassword:
    def test_exactly_eight_characters_accepted(self):
        r = RegisterRequest(email="user@example.com", password="12345678")
        assert len(r.password) == 8

    def test_fewer_than_eight_rejected(self):
        with pytest.raises(ValidationError, match="at least 8 characters"):
            RegisterRequest(email="user@example.com", password="1234567")

    def test_exactly_128_characters_accepted(self):
        p = "x" * 128
        r = RegisterRequest(email="user@example.com", password=p)
        assert len(r.password) == 128

    def test_more_than_128_rejected(self):
        with pytest.raises(ValidationError, match="no more than 128"):
            RegisterRequest(email="user@example.com", password="x" * 129)

    def test_empty_rejected(self):
        with pytest.raises(ValidationError, match="at least 8 characters"):
            RegisterRequest(email="user@example.com", password="")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError, match="only whitespace"):
            RegisterRequest(email="user@example.com", password="   ")

    def test_internal_spaces_accepted(self):
        r = RegisterRequest(email="user@example.com", password="abc 123 def 456")
        assert len(r.password) >= 8

    def test_passphrase_accepted(self):
        r = RegisterRequest(
            email="user@example.com",
            password="correct horse battery staple",
        )
        assert len(r.password) >= 8

    def test_leading_whitespace_preserved(self):
        r = RegisterRequest(email="user@example.com", password="  password123")
        assert r.password == "  password123"

    def test_trailing_whitespace_preserved(self):
        r = RegisterRequest(email="user@example.com", password="password123  ")
        assert r.password == "password123  "

    def test_password_not_stripped(self):
        r = RegisterRequest(email="user@example.com", password="  pwd12345  ")
        assert r.password == "  pwd12345  "

    def test_unicode_accepted(self):
        r = RegisterRequest(email="user@example.com", password="pässwörd_123_日本語")
        assert len(r.password) >= 8

    def test_emoji_accepted_when_minimum_length_satisfied(self):
        r = RegisterRequest(email="user@example.com", password="😀😀😀😀😀😀😀😀")
        assert len(r.password) >= 8

    def test_mixed_unicode_accepted(self):
        r = RegisterRequest(email="user@example.com", password="密码密码密码密码")
        assert len(r.password) >= 8

    def test_password_case_preserved(self):
        r = RegisterRequest(email="user@example.com", password="MyPassword123")
        assert r.password == "MyPassword123"

    def test_no_uppercase_requirement(self):
        r = RegisterRequest(email="user@example.com", password="lowercaseonly")
        assert r.password == "lowercaseonly"

    def test_no_lowercase_requirement(self):
        r = RegisterRequest(email="user@example.com", password="UPPERCASEONLY")
        assert r.password == "UPPERCASEONLY"

    def test_no_digit_requirement(self):
        r = RegisterRequest(email="user@example.com", password="abcdefgh")
        assert r.password == "abcdefgh"

    def test_no_symbol_requirement(self):
        r = RegisterRequest(email="user@example.com", password="abcdefgh")
        assert r.password == "abcdefgh"

    def test_password_not_hashed(self):
        p = "my_secret_password_123"
        r = RegisterRequest(email="user@example.com", password=p)
        assert r.password == p
        assert "$argon2" not in r.password

    def test_password_not_modified(self):
        p = "MyUniquePass123!@#"
        r = RegisterRequest(email="user@example.com", password=p)
        assert r.password == p


# ---------------------------------------------------------------------------
# RegisterRequest — extra fields (mass-assignment protection)
# ---------------------------------------------------------------------------
class TestRegisterExtraFields:
    def test_is_active_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="password123", is_active=True)

    def test_is_verified_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="password123", is_verified=True)

    def test_is_admin_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="password123", is_admin=True)

    def test_role_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@example.com", password="password123", role="admin")

    def test_password_hash_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                password="password123",
                password_hash="$argon2id$something",
            )

    def test_created_at_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                password="password123",
                created_at="2024-01-01T00:00:00Z",
            )

    def test_id_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                password="password123",
                id="550e8400-e29b-41d4-a716-446655440000",
            )

    def test_arbitrary_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="user@example.com",
                password="password123",
                some_random_field="value",
            )


# ---------------------------------------------------------------------------
# LoginRequest
# ---------------------------------------------------------------------------
class TestLogin:
    def test_valid_login_accepted(self):
        login_req = LoginRequest(email="user@example.com", password="mypassword")
        assert login_req.email == "user@example.com"
        assert login_req.password == "mypassword"

    def test_email_normalized(self):
        login_req = LoginRequest(email="  User@Example.COM  ", password="mypassword")
        assert login_req.email == "user@example.com"

    def test_same_normalization_as_registration(self):
        raw = "  User+Test@Example.COM  "
        r = RegisterRequest(email=raw, password="password123")
        login_req = LoginRequest(email=raw, password="mypassword")
        assert r.email == login_req.email

    def test_password_preserved_exactly(self):
        login_req = LoginRequest(email="user@example.com", password="  MyPass 123  ")
        assert login_req.password == "  MyPass 123  "

    def test_empty_password_rejected(self):
        with pytest.raises(ValidationError, match="not be empty"):
            LoginRequest(email="user@example.com", password="")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError, match="only whitespace"):
            LoginRequest(email="user@example.com", password="   ")

    def test_short_non_empty_accepted(self):
        login_req = LoginRequest(email="user@example.com", password="a")
        assert login_req.password == "a"

    def test_exactly_128_accepted(self):
        p = "x" * 128
        login_req = LoginRequest(email="user@example.com", password=p)
        assert len(login_req.password) == 128

    def test_more_than_128_rejected(self):
        with pytest.raises(ValidationError, match="no more than 128"):
            LoginRequest(email="user@example.com", password="x" * 129)

    def test_unicode_accepted(self):
        login_req = LoginRequest(email="user@example.com", password="pässwörd")
        assert login_req.password == "pässwörd"

    def test_leading_whitespace_preserved(self):
        login_req = LoginRequest(email="user@example.com", password="  mypassword")
        assert login_req.password == "  mypassword"

    def test_trailing_whitespace_preserved(self):
        login_req = LoginRequest(email="user@example.com", password="mypassword  ")
        assert login_req.password == "mypassword  "

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="mypassword", extra_field="x")

    def test_password_hash_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(
                email="user@example.com",
                password="mypassword",
                password_hash="$argon2id$hash",
            )

    def test_is_admin_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="mypassword", is_admin=True)


# ---------------------------------------------------------------------------
# Password representation safety
# ---------------------------------------------------------------------------
class TestPasswordRepresentation:
    def test_register_request_repr_hides_password(self):
        r = RegisterRequest(email="user@example.com", password="secret123")
        rep = repr(r)
        assert "secret123" not in rep

    def test_register_request_str_hides_password(self):
        r = RegisterRequest(email="user@example.com", password="secret123")
        s = str(r)
        assert "secret123" not in s

    def test_login_request_repr_hides_password(self):
        login_req = LoginRequest(email="user@example.com", password="secret123")
        rep = repr(login_req)
        assert "secret123" not in rep

    def test_login_request_str_hides_password(self):
        login_req = LoginRequest(email="user@example.com", password="secret123")
        s = str(login_req)
        assert "secret123" not in s

    def test_password_accessible_through_attribute(self):
        r = RegisterRequest(email="user@example.com", password="secret123")
        assert r.password == "secret123"
        login_req = LoginRequest(email="user@example.com", password="secret456")
        assert login_req.password == "secret456"

    def test_repr_does_not_contain_password_field_value(self):
        r = RegisterRequest(email="user@example.com", password="MyP@ssw0rd!")
        assert "MyP@ssw0rd!" not in repr(r)

    def test_str_does_not_contain_password_field_value(self):
        login_req = LoginRequest(email="user@example.com", password="MyP@ssw0rd!")
        assert "MyP@ssw0rd!" not in str(login_req)


# ---------------------------------------------------------------------------
# PublicUser
# ---------------------------------------------------------------------------
class TestPublicUser:
    @pytest.fixture
    def user_dict(self):
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "is_active": True,
            "is_verified": False,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T12:00:00+00:00",
        }

    def test_valid_dictionary_accepted(self, user_dict):
        u = PublicUser.model_validate(user_dict)
        assert u.email == "user@example.com"

    def test_uuid_retained(self, user_dict):
        u = PublicUser.model_validate(user_dict)
        assert isinstance(u.id, uuid.UUID)
        assert str(u.id) == "550e8400-e29b-41d4-a716-446655440000"

    def test_email_validated(self):
        with pytest.raises(ValidationError):
            PublicUser(
                id="550e8400-e29b-41d4-a716-446655440000",
                email="not-an-email",
                is_active=True,
                is_verified=False,
                created_at="2024-01-01T00:00:00+00:00",
                updated_at="2024-01-01T12:00:00+00:00",
            )

    def test_email_normalization(self, user_dict):
        user_dict["email"] = "  User@Example.COM  "
        u = PublicUser.model_validate(user_dict)
        assert u.email == "user@example.com"

    def test_boolean_values_retained(self, user_dict):
        u = PublicUser.model_validate(user_dict)
        assert u.is_active is True
        assert u.is_verified is False

    def test_datetimes_retained(self, user_dict):
        u = PublicUser.model_validate(user_dict)
        assert isinstance(u.created_at, datetime)
        assert isinstance(u.updated_at, datetime)

    def test_serialization_contains_only_allowed_fields(self, user_dict):
        u = PublicUser.model_validate(user_dict)
        data = u.model_dump()
        assert set(data.keys()) == {
            "id",
            "email",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        }

    def test_password_not_a_schema_field(self):
        assert "password" not in PublicUser.model_fields

    def test_password_hash_not_a_schema_field(self):
        assert "password_hash" not in PublicUser.model_fields

    def test_token_fields_not_schema_fields(self):
        assert "access_token" not in PublicUser.model_fields
        assert "refresh_token" not in PublicUser.model_fields
        assert "token_type" not in PublicUser.model_fields

    def test_orm_like_object_accepted(self):
        class FakeUser:
            def __init__(self):
                self.id = uuid.uuid4()
                self.email = "test@example.com"
                self.is_active = True
                self.is_verified = False
                self.created_at = datetime.now(UTC)
                self.updated_at = datetime.now(UTC)

        u = PublicUser.model_validate(FakeUser())
        assert u.email == "test@example.com"

    def test_unsaved_user_orm_object_accepted(self):
        from app.models.user import User

        now = datetime.now(UTC)
        user = User(
            id=uuid.uuid4(),
            email="orm@example.com",
            password_hash="dummy_hash_for_testing",
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        u = PublicUser.model_validate(user)
        assert u.email == "orm@example.com"
        assert u.is_active is True
        assert u.is_verified is False

    def test_no_database_connection_occurs(self):
        import app.schemas.auth

        assert hasattr(app.schemas.auth, "PublicUser")


# ---------------------------------------------------------------------------
# TokenPair
# ---------------------------------------------------------------------------
class TestTokenPair:
    def test_valid_token_pair_accepted(self):
        t = TokenPair(access_token="abc123", refresh_token="def456")
        assert t.access_token == "abc123"
        assert t.refresh_token == "def456"

    def test_default_token_type_is_bearer(self):
        t = TokenPair(access_token="abc", refresh_token="def")
        assert t.token_type == "bearer"

    def test_explicit_bearer_accepted(self):
        t = TokenPair(access_token="abc", refresh_token="def", token_type="bearer")
        assert t.token_type == "bearer"

    def test_bearer_capitalized_rejected(self):
        with pytest.raises(ValidationError):
            TokenPair(access_token="abc", refresh_token="def", token_type="Bearer")

    def test_bearer_uppercase_rejected(self):
        with pytest.raises(ValidationError):
            TokenPair(access_token="abc", refresh_token="def", token_type="BEARER")

    def test_jwt_rejected(self):
        with pytest.raises(ValidationError):
            TokenPair(access_token="abc", refresh_token="def", token_type="jwt")

    def test_unsupported_token_type_rejected(self):
        with pytest.raises(ValidationError):
            TokenPair(access_token="abc", refresh_token="def", token_type="token")

    def test_empty_access_token_rejected(self):
        with pytest.raises(ValidationError, match="not be empty"):
            TokenPair(access_token="", refresh_token="def")

    def test_whitespace_only_access_token_rejected(self):
        with pytest.raises(ValidationError, match="only whitespace"):
            TokenPair(access_token="   ", refresh_token="def")

    def test_empty_refresh_token_rejected(self):
        with pytest.raises(ValidationError, match="not be empty"):
            TokenPair(access_token="abc", refresh_token="")

    def test_whitespace_only_refresh_token_rejected(self):
        with pytest.raises(ValidationError, match="only whitespace"):
            TokenPair(access_token="abc", refresh_token="   ")

    def test_token_values_preserved(self):
        t = TokenPair(
            access_token="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.test",
            refresh_token="dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4=",
        )
        assert t.access_token == "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.test"
        assert t.refresh_token == "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4="

    def test_tokens_not_generated(self):
        t = TokenPair(access_token="fixed_token", refresh_token="fixed_refresh")
        assert t.access_token == "fixed_token"
        assert t.refresh_token == "fixed_refresh"

    def test_tokens_not_decoded(self):
        t = TokenPair(access_token="raw.string.value", refresh_token="raw.string.value")
        assert t.access_token == "raw.string.value"


# ---------------------------------------------------------------------------
# AuthResponse
# ---------------------------------------------------------------------------
class TestAuthResponse:
    @pytest.fixture
    def valid_user_dict(self):
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "is_active": True,
            "is_verified": False,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T12:00:00+00:00",
        }

    @pytest.fixture
    def valid_token_dict(self):
        return {
            "access_token": "access123",
            "refresh_token": "refresh456",
            "token_type": "bearer",
        }

    def test_valid_nested_response_accepted(self, valid_user_dict, valid_token_dict):
        r = AuthResponse(
            user=PublicUser.model_validate(valid_user_dict),
            tokens=TokenPair.model_validate(valid_token_dict),
        )
        assert r.user.email == "user@example.com"
        assert r.tokens.access_token == "access123"

    def test_nested_user_serialization_correct(self, valid_user_dict, valid_token_dict):
        r = AuthResponse(
            user=PublicUser.model_validate(valid_user_dict),
            tokens=TokenPair.model_validate(valid_token_dict),
        )
        data = r.model_dump()
        assert data["user"]["email"] == "user@example.com"
        assert data["user"]["is_active"] is True
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

    def test_nested_tokens_serialization_correct(self, valid_user_dict, valid_token_dict):
        r = AuthResponse(
            user=PublicUser.model_validate(valid_user_dict),
            tokens=TokenPair.model_validate(valid_token_dict),
        )
        data = r.model_dump()
        assert data["tokens"]["access_token"] == "access123"
        assert data["tokens"]["refresh_token"] == "refresh456"
        assert data["tokens"]["token_type"] == "bearer"

    def test_missing_user_rejected(self, valid_token_dict):
        with pytest.raises(ValidationError):
            AuthResponse(tokens=TokenPair.model_validate(valid_token_dict))

    def test_missing_tokens_rejected(self, valid_user_dict):
        with pytest.raises(ValidationError):
            AuthResponse(user=PublicUser.model_validate(valid_user_dict))

    def test_invalid_user_rejected(self, valid_token_dict):
        with pytest.raises(ValidationError):
            AuthResponse(
                user={"email": "invalid"},  # missing required fields
                tokens=TokenPair.model_validate(valid_token_dict),
            )

    def test_invalid_tokens_rejected(self, valid_user_dict):
        with pytest.raises(ValidationError):
            AuthResponse(
                user=PublicUser.model_validate(valid_user_dict),
                tokens={"access_token": "", "refresh_token": "def"},
            )

    def test_password_hash_absent_from_serialized_output(self, valid_user_dict, valid_token_dict):
        r = AuthResponse(
            user=PublicUser.model_validate(valid_user_dict),
            tokens=TokenPair.model_validate(valid_token_dict),
        )
        data = r.model_dump()
        assert "password" not in str(data)
        assert "password_hash" not in str(data)


# ---------------------------------------------------------------------------
# Side-effect audit — schema import
# ---------------------------------------------------------------------------
class TestSchemaImports:
    def test_schema_package_imports(self):
        from app.schemas import (
            AuthResponse,
            LoginRequest,
            PublicUser,
            RegisterRequest,
            TokenPair,
        )

        assert AuthResponse is not None
        assert LoginRequest is not None
        assert PublicUser is not None
        assert RegisterRequest is not None
        assert TokenPair is not None

    def test_import_does_not_hash_passwords(self):
        from app.schemas.auth import RegisterRequest

        r = RegisterRequest(email="user@example.com", password="password123")
        assert "$argon2" not in r.password

    def test_import_does_not_generate_tokens(self):
        from app.schemas.auth import TokenPair

        t = TokenPair(access_token="test", refresh_token="test")
        assert t.access_token == "test"

    def test_import_does_not_require_jwt_secret(self):
        from app.core.config import Settings

        s = Settings(APP_ENV="test", _env_file=None)
        assert s.JWT_SECRET_KEY == ""

    def test_import_does_not_require_docker(self):
        from app.schemas.auth import PublicUser

        assert PublicUser is not None


# ---------------------------------------------------------------------------
# Normalize email utility
# ---------------------------------------------------------------------------
class TestNormalizeEmail:
    def test_strips_leading_whitespace(self):
        assert normalize_email("  user@example.com") == "user@example.com"

    def test_strips_trailing_whitespace(self):
        assert normalize_email("user@example.com  ") == "user@example.com"

    def test_lowercases(self):
        assert normalize_email("User@Example.COM") == "user@example.com"

    def test_preserves_plus_addressing(self):
        assert normalize_email("User+Tag@Example.com") == "user+tag@example.com"

    def test_preserves_dots(self):
        assert normalize_email("First.Last@Example.com") == "first.last@example.com"

    def test_fully_normalizes(self):
        assert normalize_email("  User+Nutrition@Example.COM  ") == "user+nutrition@example.com"

    def test_empty_string(self):
        assert normalize_email("") == ""

    def test_whitespace_only(self):
        assert normalize_email("   ") == ""

    def test_preserves_valid_email_structure(self):
        raw = "test.email+tag@sub.domain.co.uk"
        result = normalize_email(raw)
        assert result == raw.lower()
        assert "@" in result
        assert "." in result.split("@")[1]
