"""SQLAlchemy 2.0 asynchronous engine and session factory for NIRMAYA."""

import time
from typing import Any, AsyncGenerator, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

# Engine configuration arguments with connection pooling
_engine_kwargs: Dict[str, Any] = {
    "echo": settings.DATABASE_ECHO,
}

# Apply connection pooling options for non-sqlite backends
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,
        }
    )

# Global asynchronous engine instance
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **_engine_kwargs,
)

# Async session factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an asynchronous database session.

    Ensures transaction integrity with automatic rollback on exception
    and deterministic session closure upon request completion.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health(
    engine: AsyncEngine | None = None,
) -> Dict[str, Any]:
    """Probe database connectivity and measure query round-trip latency.

    Returns a structured dictionary with status ('healthy' or 'unreachable'),
    latency in milliseconds, dialect name, and error diagnostics if failed.
    """
    target_engine = engine or async_engine
    start_time = time.perf_counter()
    try:
        async with target_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "database_type": target_engine.dialect.name,
            "error": None,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "unreachable",
            "latency_ms": latency_ms,
            "database_type": target_engine.dialect.name,
            "error": str(exc),
        }
