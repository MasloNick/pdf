"""Database engine and session factories."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Async engine (for FastAPI endpoints)
async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_size=20)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine (for Celery workers / Alembic)
sync_engine = create_engine(settings.DATABASE_SYNC_URL, echo=settings.DEBUG, pool_size=10)
SyncSessionLocal = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
