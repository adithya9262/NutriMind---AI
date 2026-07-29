import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings
from app.main import create_app


class TestConfigAndImportSafety:
    async def test_app_imports_without_database_url(self):
        import importlib

        reloaded = importlib.import_module("app.main")
        assert hasattr(reloaded, "create_app")

    async def test_app_factory_works_without_database(self):
        settings = Settings(APP_ENV="test", DATABASE_URL="")
        app = create_app(settings=settings)
        assert app is not None

    async def test_health_endpoint_works_without_database(self):
        settings = Settings(APP_ENV="test", DATABASE_URL="")
        app = create_app(settings=settings)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_db_modules_import_without_connecting(self):
        from app.db import base, dependencies, session

        assert base is not None
        assert session is not None
        assert dependencies is not None

    async def test_db_import_does_not_create_engine(self):
        from app.db.session import db_manager

        assert db_manager.is_initialized is False

    async def test_missing_config_fails_only_when_access_requested(self):
        from app.db.session import db_manager

        with pytest.raises(RuntimeError, match="Database engine is not initialized"):
            _ = db_manager.engine

    async def test_missing_session_factory_fails_only_when_access_requested(self):
        from app.db.session import db_manager

        with pytest.raises(RuntimeError, match="Database session factory is not initialized"):
            _ = db_manager.session_factory

    async def test_initialize_with_empty_url_raises(self):
        from app.db.session import db_manager as mgr

        with pytest.raises(ValueError, match="DATABASE_URL is not configured"):
            mgr.initialize("")

    async def test_error_does_not_expose_credentials(self):
        from app.db.session import db_manager as mgr

        with pytest.raises(ValueError) as exc:
            mgr.initialize("")
        msg = str(exc.value)
        assert "postgresql" not in msg
        assert "://" not in msg
        assert "@" not in msg or "DATABASE_URL" in msg


class TestDeclarativeBase:
    def test_base_is_declarative_base(self):
        from app.db.base import Base

        assert isinstance(Base, type)
        assert issubclass(Base, DeclarativeBase)

    def test_base_metadata_has_application_tables(self):
        from app.db.base import Base

        assert len(Base.metadata.tables) >= 2


class TestEngineAndSession:
    async def test_engine_initialization_is_explicit(self):
        from app.db.session import db_manager as mgr

        assert mgr.is_initialized is False
        mgr.initialize("postgresql+asyncpg://u:p@localhost:5432/db")
        assert mgr.is_initialized is True
        await mgr.dispose()

    async def test_engine_is_reused(self):
        from app.db.session import db_manager as mgr

        mgr.initialize("postgresql+asyncpg://u:p@localhost:5432/db")
        engine1 = mgr.engine
        engine2 = mgr.engine
        assert engine1 is engine2
        await mgr.dispose()

    async def test_session_factory_is_reused(self):
        from app.db.session import db_manager as mgr

        mgr.initialize("postgresql+asyncpg://u:p@localhost:5432/db")
        sf1 = mgr.session_factory
        sf2 = mgr.session_factory
        assert sf1 is sf2
        await mgr.dispose()

    async def test_engine_disposal_is_supported(self):
        from app.db.session import db_manager as mgr

        mgr.initialize("postgresql+asyncpg://u:p@localhost:5432/db")
        assert mgr.is_initialized is True
        await mgr.dispose()
        assert mgr.is_initialized is False

    async def test_after_disposal_engine_raises(self):
        from app.db.session import db_manager as mgr

        mgr.initialize("postgresql+asyncpg://u:p@localhost:5432/db")
        await mgr.dispose()
        with pytest.raises(RuntimeError, match="Database engine is not initialized"):
            _ = mgr.engine


class TestSessionDependency:
    async def _init_db_with_mock_session(self):
        from unittest.mock import AsyncMock

        from app.db.dependencies import get_db_session
        from app.db.session import db_manager as mgr

        mgr.initialize("postgresql+asyncpg://u:p@localhost:5432/db")
        mock_session = AsyncMock()
        mock_session.closed = False
        mgr._session_factory = lambda: mock_session  # type: ignore[attr-defined]
        return mgr, get_db_session(), mock_session

    async def test_get_db_session_yields_session(self):
        mgr, gen, mock_session = await self._init_db_with_mock_session()
        session = await anext(gen)
        assert session is mock_session
        with pytest.raises(StopAsyncIteration):
            await anext(gen)
        mock_session.close.assert_awaited_once()
        await mgr.dispose()

    async def test_session_closes_after_use(self):
        mgr, gen, mock_session = await self._init_db_with_mock_session()
        await anext(gen)
        with pytest.raises(StopAsyncIteration):
            await anext(gen)
        mock_session.close.assert_awaited_once()
        await mgr.dispose()

    async def test_exception_triggers_rollback(self):
        mgr, gen, mock_session = await self._init_db_with_mock_session()
        session = await anext(gen)
        assert session is mock_session
        with pytest.raises(ValueError, match="test error"):
            await gen.athrow(ValueError("test error"))
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()
        await mgr.dispose()

    async def test_sessions_do_not_auto_commit(self):
        mgr, gen, mock_session = await self._init_db_with_mock_session()
        await anext(gen)
        with pytest.raises(StopAsyncIteration):
            await anext(gen)
        mock_session.commit.assert_not_awaited()
        await mgr.dispose()

    async def test_original_exception_is_re_raised(self):
        mgr, gen, mock_session = await self._init_db_with_mock_session()
        await anext(gen)
        with pytest.raises(RuntimeError) as exc_info:
            await gen.athrow(RuntimeError("original"))
        assert "original" in str(exc_info.value)
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()
        await mgr.dispose()
