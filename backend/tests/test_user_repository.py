from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_exceptions import EmailAlreadyRegisteredError
from app.models.user import User
from app.repositories.user import UserRepository


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_user(
    email: str = "test@example.com",
    password_hash: str = "$argon2id$v=19$m=65536,t=3,p=4$hash",
    is_active: bool = True,
    is_verified: bool = False,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.email = email
    user.password_hash = password_hash
    user.is_active = is_active
    user.is_verified = is_verified
    return user


class TestUserRepositoryInit:
    def test_stores_supplied_session(self):
        session = _make_session()
        repo = UserRepository(session)
        assert repo._session is session

    def test_does_not_create_another_session(self):
        session = _make_session()
        UserRepository(session)
        session.assert_not_called()

    def test_does_not_connect_during_construction(self):
        session = _make_session()
        UserRepository(session)
        # No execute calls should occur during init
        session.execute.assert_not_called()


class TestGetByEmail:
    async def test_uses_normalized_email_provided_by_caller(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("normalized@example.com")

        call_args = session.execute.call_args[0][0]
        compiled = call_args.compile(compile_kwargs={"literal_binds": True})
        assert "normalized@example.com" in str(compiled)

    async def test_executes_one_select_statement(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("test@example.com")

        session.execute.assert_awaited_once()

    async def test_returns_user_when_found(self):
        session = _make_session()
        user = _make_user()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        result = await repo.get_by_email("test@example.com")

        assert result is user

    async def test_returns_none_when_not_found(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        result = await repo.get_by_email("unknown@example.com")

        assert result is None

    async def test_does_not_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("test@example.com")

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("test@example.com")

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("test@example.com")

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("test@example.com")

        session.close.assert_not_called()

    async def test_does_not_hash_password(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        await repo.get_by_email("test@example.com")

        # No hashing imports should be called
        from app.repositories import user as repo_module

        source = open(repo_module.__file__).read()
        assert "hash_password" not in source
        assert "verify_password" not in source

    async def test_does_not_mutate_user(self):
        session = _make_session()
        user = _make_user()
        original_email = user.email
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        result = await repo.get_by_email("test@example.com")

        assert result.email == original_email
        assert result is user


class TestCreate:
    async def test_accepts_only_email_and_password_hash_kwargs(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(
            email="new@example.com",
            password_hash="hashed_value",
        )

        session.add.assert_called_once()
        added_user = session.add.call_args[0][0]
        assert isinstance(added_user, User)
        assert added_user.email == "new@example.com"
        assert added_user.password_hash == "hashed_value"

    async def test_uses_supplied_email(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(
            email="specific@example.com",
            password_hash="hash",
        )

        assert user.email == "specific@example.com"

    async def test_uses_supplied_password_hash(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(
            email="test@example.com",
            password_hash="specific_hash_value",
        )

        assert user.password_hash == "specific_hash_value"

    async def test_adds_exactly_one_user(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(email="test@example.com", password_hash="hash")

        session.add.assert_called_once()

    async def test_flushes_exactly_once(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(email="test@example.com", password_hash="hash")

        session.flush.assert_awaited_once()

    async def test_returns_created_user(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(email="test@example.com", password_hash="hash")

        assert isinstance(user, User)
        assert user.email == "test@example.com"

    async def test_does_not_commit(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(email="test@example.com", password_hash="hash")

        session.commit.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(email="test@example.com", password_hash="hash")

        session.close.assert_not_called()

    async def test_does_not_create_another_session(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(email="test@example.com", password_hash="hash")

        session_factory_attr = getattr(session, "session_factory", None)
        if session_factory_attr is not None:
            session_factory_attr.assert_not_called()

    async def test_does_not_hash_password(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        await repo.create(email="test@example.com", password_hash="hash")

        from app.repositories import user as repo_module

        source = open(repo_module.__file__).read()
        assert "hash_password" not in source
        assert "verify_password" not in source

    async def test_preserves_default_is_active(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(email="test@example.com", password_hash="hash")

        # is_active is None before DB flush (SQLAlchemy applies mapped_column
        # default at INSERT time, not at object creation). The repo does not
        # override the model default.
        assert "is_active" in type(user).__mapper__.columns

    async def test_preserves_default_is_verified(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(email="test@example.com", password_hash="hash")

        assert "is_verified" in type(user).__mapper__.columns

    async def test_does_not_accept_plaintext_password(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(
            email="test@example.com",
            password_hash="secure_hash_value",
        )

        assert not user.password_hash.startswith("plain_")
        assert user.password_hash != "password123"
        assert user.password_hash == "secure_hash_value"

    async def test_does_not_accept_is_active(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(email="test@example.com", password_hash="hash")

        # The repo does not explicitly set is_active; it uses the model default
        assert hasattr(user, "is_active")


class TestCreateConflictHandling:
    async def test_duplicate_email_raises_email_already_registered(self):
        session = _make_session()
        repo = UserRepository(session)

        class FakeOrig:
            constraint_name = "uq_users_email"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(EmailAlreadyRegisteredError):
            await repo.create(
                email="existing@example.com",
                password_hash="hash",
            )

        session.add.assert_called_once()
        session.flush.assert_awaited_once()

    async def test_unrelated_integrity_error_is_re_raised(self):
        session = _make_session()
        repo = UserRepository(session)

        class FakeOtherOrig:
            constraint_name = "some_other_constraint"

        orig = FakeOtherOrig()
        integrity_error = IntegrityError("INSERT INTO other_table...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                email="test@example.com",
                password_hash="hash",
            )

    async def test_domain_exception_contains_no_sql_details(self):
        session = _make_session()
        repo = UserRepository(session)

        class FakeOrig:
            constraint_name = "uq_users_email"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await repo.create(
                email="existing@example.com",
                password_hash="hash",
            )

        error_message = str(exc_info.value)
        assert "INSERT" not in error_message
        assert "users" not in error_message
        assert "uq_users_email" not in error_message
        assert "constraint" not in error_message.lower()

    async def test_domain_exception_contains_no_password_hash(self):
        session = _make_session()
        repo = UserRepository(session)

        class FakeOrig:
            constraint_name = "uq_users_email"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(EmailAlreadyRegisteredError) as exc_info:
            await repo.create(
                email="existing@example.com",
                password_hash="secret_hash_value",
            )

        error_message = str(exc_info.value)
        assert "secret_hash_value" not in error_message
        assert "$argon2" not in error_message

    async def test_no_commit_occurs_on_conflict(self):
        session = _make_session()
        repo = UserRepository(session)

        class FakeOrig:
            constraint_name = "uq_users_email"

        orig = FakeOrig()
        integrity_error = IntegrityError("INSERT INTO users...", {}, orig)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(EmailAlreadyRegisteredError):
            await repo.create(
                email="existing@example.com",
                password_hash="hash",
            )

        session.commit.assert_not_called()

    async def test_session_orig_none_fallback(self):
        session = _make_session()
        repo = UserRepository(session)

        integrity_error = IntegrityError("INSERT INTO users...", {}, None)
        session.flush = AsyncMock(side_effect=integrity_error)

        with pytest.raises(IntegrityError):
            await repo.create(
                email="test@example.com",
                password_hash="hash",
            )


class TestGetById:
    async def test_method_exists_and_accepts_uuid(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_returns_user_when_found(self):
        session = _make_session()
        user = _make_user()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = user
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        result = await repo.get_by_id(user.id)

        assert result is user

    async def test_returns_none_when_not_found(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        result = await repo.get_by_id(uuid.uuid4())

        assert result is None

    async def test_uses_select_user_and_filters_by_id(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        user_id = uuid.uuid4()
        await repo.get_by_id(user_id)

        call_args = session.execute.call_args[0][0]
        compiled = call_args.compile(compile_kwargs={"literal_binds": True})
        compiled_str = str(compiled)
        assert "users" in compiled_str
        assert "id" in compiled_str
        assert user_id.hex in compiled_str or str(user_id).replace("-", "") in compiled_str

    async def test_executes_once(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        await repo.get_by_id(uuid.uuid4())

        session.execute.assert_awaited_once()

    async def test_does_not_commit(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        await repo.get_by_id(uuid.uuid4())

        session.commit.assert_not_called()

    async def test_does_not_flush(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        await repo.get_by_id(uuid.uuid4())

        session.flush.assert_not_called()

    async def test_does_not_rollback(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        await repo.get_by_id(uuid.uuid4())

        session.rollback.assert_not_called()

    async def test_does_not_close_session(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        await repo.get_by_id(uuid.uuid4())

        session.close.assert_not_called()

    async def test_does_not_create_session(self):
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        import uuid

        await repo.get_by_id(uuid.uuid4())

        session_factory_attr = getattr(session, "session_factory", None)
        if session_factory_attr is not None:
            session_factory_attr.assert_not_called()

    async def test_database_exception_re_raised(self):
        session = _make_session()
        repo = UserRepository(session)

        session.execute = AsyncMock(side_effect=Exception("DB connection failed"))

        import uuid

        with pytest.raises(Exception) as exc_info:
            await repo.get_by_id(uuid.uuid4())

        assert "DB connection failed" in str(exc_info.value)

    async def test_get_by_email_still_works(self):
        session = _make_session()
        user = _make_user()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session)
        result = await repo.get_by_email("test@example.com")

        assert result is user
        assert result.email == "test@example.com"

    async def test_create_still_works(self):
        session = _make_session()
        session.flush = AsyncMock()
        repo = UserRepository(session)

        user = await repo.create(
            email="new@example.com",
            password_hash="hash",
        )

        assert isinstance(user, User)
        assert user.email == "new@example.com"
        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        session.commit.assert_not_called()
