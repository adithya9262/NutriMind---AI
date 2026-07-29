from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .session import db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = db_manager.session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
