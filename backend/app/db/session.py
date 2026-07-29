from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseManager:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self, url: str) -> None:
        if not url:
            raise ValueError(
                "DATABASE_URL is not configured. Set DATABASE_URL in your environment or .env file."
            )
        self._engine = create_async_engine(url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database engine is not initialized")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("Database session factory is not initialized")
        return self._session_factory

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def is_initialized(self) -> bool:
        return self._engine is not None


db_manager = DatabaseManager()


async def check_database_connectivity() -> bool:
    engine = db_manager.engine
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True
