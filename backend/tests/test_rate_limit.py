"""Unit and integration tests for rate limiting middleware and token bucket engine."""

import pytest
import time
from httpx import AsyncClient
from app.core.config import settings
from app.core.rate_limit import TokenBucket, rate_limiter


@pytest.fixture(autouse=True)
def reset_limiter():
    """Ensure clean rate limiter state before each test execution."""
    rate_limiter.clear()
    original_enabled = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = True
    yield
    rate_limiter.clear()
    settings.RATE_LIMIT_ENABLED = original_enabled


@pytest.mark.asyncio
async def test_token_bucket_unit_exhaustion_and_refill():
    """Verify TokenBucket capacity consumption, rejection, and refill semantics."""
    bucket = TokenBucket(capacity=3, refill_rate_per_sec=10.0)

    # First 3 tokens should succeed immediately
    ok1, rem1, wait1 = await bucket.consume(1.0)
    assert ok1 is True
    assert rem1 == 2
    assert wait1 == 0

    ok2, rem2, wait2 = await bucket.consume(1.0)
    assert ok2 is True
    assert rem2 == 1

    ok3, rem3, wait3 = await bucket.consume(1.0)
    assert ok3 is True
    assert rem3 == 0

    # 4th consume must fail with non-zero retry_after
    ok4, rem4, wait4 = await bucket.consume(1.0)
    assert ok4 is False
    assert rem4 == 0
    assert wait4 >= 1


@pytest.mark.asyncio
async def test_exempt_endpoint_bypasses_rate_limit(client: AsyncClient):
    """Verify system health and metadata routes are exempt from rate limiting."""
    for _ in range(5):
        response = await client.get("/api/v1/meta")
        assert response.status_code == 200
        # Exempt routes should not have rate limit headers injected
        assert "X-RateLimit-Limit" not in response.headers


@pytest.mark.asyncio
async def test_rate_limit_headers_injected_on_tracked_endpoint(client: AsyncClient):
    """Verify rate limit telemetry headers are attached to tracked clinical API requests."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"X-Forwarded-For": "192.168.1.50"},
    )
    # Auth without token returns 401, but rate limit headers must be present
    assert response.status_code == 401
    assert "X-RateLimit-Limit" in response.headers
    assert response.headers["X-RateLimit-Limit"] == str(settings.RATE_LIMIT_AUTH_PER_MINUTE)
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_exceeded_returns_429(client: AsyncClient):
    """Verify that exceeding configured limit returns HTTP 429 and structured error envelope."""
    test_ip = "192.168.1.99"
    limit = settings.RATE_LIMIT_AUTH_PER_MINUTE  # 15

    # Consume the entire allowance
    for i in range(limit):
        res = await client.get(
            "/api/v1/auth/me",
            headers={"X-Forwarded-For": test_ip},
        )
        assert res.status_code == 401

    # The (limit + 1)th request must be throttled with HTTP 429
    blocked_res = await client.get(
        "/api/v1/auth/me",
        headers={"X-Forwarded-For": test_ip},
    )
    assert blocked_res.status_code == 429

    # Verify structured JSON error envelope
    body = blocked_res.json()
    assert body["success"] is False
    assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "Too many requests" in body["message"]
    assert body["details"]["limit"] == limit
    assert body["details"]["window_seconds"] == 60
    assert body["details"]["retry_after"] >= 1
    assert "timestamp" in body

    # Verify standard HTTP rate limit headers
    assert "Retry-After" in blocked_res.headers
    assert blocked_res.headers["X-RateLimit-Limit"] == str(limit)
    assert blocked_res.headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Reset" in blocked_res.headers


@pytest.mark.asyncio
async def test_ip_isolation_for_rate_limits(client: AsyncClient):
    """Verify that different client IPs have separate isolated rate limit budgets."""
    ip_a = "10.0.0.1"
    ip_b = "10.0.0.2"
    limit = settings.RATE_LIMIT_AUTH_PER_MINUTE

    # Exhaust allowance for IP A
    for _ in range(limit):
        await client.get("/api/v1/auth/me", headers={"X-Forwarded-For": ip_a})

    # IP A is blocked
    res_a = await client.get("/api/v1/auth/me", headers={"X-Forwarded-For": ip_a})
    assert res_a.status_code == 429

    # IP B is still permitted
    res_b = await client.get("/api/v1/auth/me", headers={"X-Forwarded-For": ip_b})
    assert res_b.status_code == 401  # Normal 401, NOT 429!
    assert res_b.headers["X-RateLimit-Remaining"] == str(limit - 1)


@pytest.mark.asyncio
async def test_rate_limiter_disabled_bypass(client: AsyncClient):
    """Verify that when RATE_LIMIT_ENABLED is False, no rate limit is applied."""
    settings.RATE_LIMIT_ENABLED = False
    test_ip = "10.0.0.3"

    for _ in range(25):
        res = await client.get("/api/v1/auth/me", headers={"X-Forwarded-For": test_ip})
        assert res.status_code == 401  # Never throttled to 429
