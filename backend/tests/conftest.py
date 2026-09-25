"""Pytest fixtures and test client setup."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from app.main import app
from app.core.rate_limit import rate_limiter


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client fixture bound to the NIRMAYA FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture(autouse=True)
def clean_rate_limit_state():
    """Ensure clean rate limiting token buckets between test executions."""
    rate_limiter.clear()
    yield
    rate_limiter.clear()
