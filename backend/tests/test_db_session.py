"""Unit test suite for SQLAlchemy 2.0 async session and health ping utility."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.session import check_db_health, get_db


@pytest.mark.asyncio
async def test_check_db_health_success_with_sqlite() -> None:
    """Verify check_db_health returns healthy status and latency with an active engine."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    probe = await check_db_health(engine=test_engine)

    assert probe["status"] == "healthy"
    assert probe["database_type"] == "sqlite"
    assert probe["error"] is None
    assert isinstance(probe["latency_ms"], float)
    assert probe["latency_ms"] >= 0.0

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_check_db_health_failure_handling() -> None:
    """Verify check_db_health gracefully catches connection errors without raising exceptions."""
    broken_engine = create_async_engine(
        "postgresql+asyncpg://invalid_user:invalid_pass@127.0.0.1:59999/nonexistent",
        echo=False,
    )

    probe = await check_db_health(engine=broken_engine)

    assert probe["status"] == "unreachable"
    assert probe["database_type"] == "postgresql"
    assert probe["error"] is not None

    await broken_engine.dispose()


@pytest.mark.asyncio
async def test_get_db_session_generator_lifecycle() -> None:
    """Verify get_db dependency yields an active session and closes it cleanly."""
    gen = get_db()
    session = await anext(gen)

    assert isinstance(session, AsyncSession)
    assert session.is_active

    # Complete the generator
    with pytest.raises(StopAsyncIteration):
        await anext(gen)


@pytest.mark.asyncio
async def test_get_db_session_rollback_on_exception() -> None:
    """Verify get_db dependency issues rollback when an exception occurs."""
    gen = get_db()
    session = await anext(gen)

    assert isinstance(session, AsyncSession)

    # Throw exception into generator to trigger rollback block
    with pytest.raises(RuntimeError, match="Clinical transaction simulated error"):
        await gen.athrow(RuntimeError("Clinical transaction simulated error"))
