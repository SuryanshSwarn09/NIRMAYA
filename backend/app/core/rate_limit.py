"""Rate limiting middleware and token bucket engine for NIRMAYA API.

Provides sliding-window token-bucket rate limiting across:
1. Authentication endpoints (/api/v1/auth/*) - strict brute-force protection.
2. Clinical & Data endpoints (/api/v1/*) - general API stability protection.
3. System probes & docs exemptions (/api/v1/health, /docs, etc.).
"""

import time
import math
import asyncio
from typing import Dict, Tuple, Optional
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.config import settings
from app.core.logging import logger


class TokenBucket:
    """Thread/coroutine safe token bucket rate tracker."""

    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(capacity)
        self.last_updated = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, amount: float = 1.0) -> Tuple[bool, int, int]:
        """Attempt to consume tokens.

        Returns:
            Tuple of (is_allowed, remaining_tokens, retry_after_seconds)
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_updated
            self.last_updated = now

            # Replenish tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

            if self.tokens >= amount:
                self.tokens -= amount
                remaining = max(0, int(self.tokens))
                return True, remaining, 0
            else:
                deficit = amount - self.tokens
                retry_after = max(1, math.ceil(deficit / self.refill_rate))
                return False, 0, retry_after


class RateLimiter:
    """Central registry and policy manager for API rate limits."""

    EXEMPT_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        f"{settings.API_V1_STR}/openapi.json",
        f"{settings.API_V1_STR}/health",
        f"{settings.API_V1_STR}/health/live",
        f"{settings.API_V1_STR}/health/ready",
        f"{settings.API_V1_STR}/meta",
    }

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()

    def clear(self) -> None:
        """Clear all active rate limit buckets (useful for test resets)."""
        self._buckets.clear()

    def _resolve_bucket_params(self, path: str) -> Tuple[str, int]:
        """Determine rate limit tier based on request path.

        Returns:
            Tuple of (tier_name, capacity_per_minute)
        """
        if path.startswith(f"{settings.API_V1_STR}/auth"):
            return "auth", settings.RATE_LIMIT_AUTH_PER_MINUTE
        return "api", settings.RATE_LIMIT_API_PER_MINUTE

    def _get_client_identifier(self, request: Request) -> str:
        """Derive client identifier from IP and Authorization token sub claim if available."""
        # Check IP address (accounting for reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        # Check if authenticated user subject is attached to request state
        user_sub = getattr(request.state, "user_sub", None)
        if user_sub:
            return f"{client_ip}:{user_sub}"

        return client_ip

    async def check(self, request: Request) -> Tuple[bool, int, int, int]:
        """Assess whether the inbound request conforms to rate limits.

        Returns:
            Tuple of (is_allowed, limit, remaining, retry_after)
        """
        path = request.url.path

        # Bypass rate limiting if disabled or path is exempt
        if not settings.RATE_LIMIT_ENABLED or path in self.EXEMPT_PATHS:
            return True, settings.RATE_LIMIT_API_PER_MINUTE, settings.RATE_LIMIT_API_PER_MINUTE, 0

        tier, limit = self._resolve_bucket_params(path)
        client_id = self._get_client_identifier(request)
        bucket_key = f"{tier}:{client_id}"

        refill_rate = limit / 60.0

        async with self._lock:
            if bucket_key not in self._buckets:
                self._buckets[bucket_key] = TokenBucket(
                    capacity=limit,
                    refill_rate_per_sec=refill_rate,
                )
            bucket = self._buckets[bucket_key]

        allowed, remaining, retry_after = await bucket.consume(1.0)
        return allowed, limit, remaining, retry_after


# Global singleton rate limiter instance
rate_limiter = RateLimiter()


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware enforcing token-bucket rate limiting."""

    async def dispatch(self, request: Request, call_next) -> Response:
        allowed, limit, remaining, retry_after = await rate_limiter.check(request)

        # Calculate standard rate limit headers
        now_epoch = int(time.time())
        reset_epoch = now_epoch + (retry_after if not allowed else 60)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {request.client.host if request.client else 'unknown'} "
                f"requested {request.url.path} (Limit: {limit}/min, Retry-After: {retry_after}s)"
            )
            response = JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Rate limit exceeded ({limit} requests/min). Please retry after {retry_after} second(s).",
                    "details": {
                        "retry_after": retry_after,
                        "limit": limit,
                        "window_seconds": 60,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch),
                },
            )
            return response

        # Proceed with normal request dispatch
        response: Response = await call_next(request)

        # Append rate limit telemetry headers to successful responses (if path was tracked)
        if request.url.path not in rate_limiter.EXEMPT_PATHS and settings.RATE_LIMIT_ENABLED:
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_epoch)

        return response
