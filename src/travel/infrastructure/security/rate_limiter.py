"""Redis-backed sliding-window Rate Limiter ASGI middleware.

Algorithm: Sliding Window Log (Redis Sorted Set per key)
---------------------------------------------------------
For each unique identifier (IP address), we keep a Redis Sorted Set where
each member is a unique request ID and the score is the request timestamp
(unix float).  On every request:

  1. Remove members older than the window.
  2. Count remaining members.
  3. If count >= limit → return 429 with Retry-After header.
  4. Otherwise add current request and proceed.

Two tiers are enforced independently:

* **Global tier** — 50 req / 60 s per IP (configurable).
* **Search tier** — 5 req / 1 s per IP, applied only to paths
  matching ``SEARCH_PATH_PREFIXES``.

Keys have an automatic TTL (``window * 2``) so they self-clean even if
the sliding-window logic misses edge cases.

Usage (registered in ``app.py``):
    from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, redis_url="redis://localhost:6379/0")
"""
from __future__ import annotations

import time
import uuid
from typing import Final

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from travel.config import get_settings

# Paths that fall under the stricter search-tier limit.
# Any request whose path *starts with* one of these gets the tighter cap.
_SEARCH_PATH_PREFIXES: Final[tuple[str, ...]] = (
    "/api/v1/flights",
    "/api/v1/trains",
    "/api/v1/accommodations",
)

# Window durations in seconds
_GLOBAL_WINDOW: Final[int] = 60   # 1 minute
_SEARCH_WINDOW: Final[float] = 1.0  # 1 second


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For from trusted proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the leftmost (client) IP, strip whitespace
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware enforcing two-tier sliding-window rate limiting via Redis.

    Parameters
    ----------
    app:
        The inner ASGI application.
    redis_url:
        Redis connection URL.  Defaults to ``Settings.redis_url``.
    """

    def __init__(self, app: ASGIApp, redis_url: str | None = None) -> None:
        super().__init__(app)
        cfg = get_settings()
        url = redis_url or cfg.redis_url
        self._redis: aioredis.Redis = aioredis.from_url(  # type: ignore[type-arg]
            url, decode_responses=True
        )
        self._enabled = cfg.rate_limit_enabled
        self._global_limit = cfg.rate_limit_global_requests
        self._search_limit = cfg.rate_limit_search_requests

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self._enabled:
            return await call_next(request)

        ip = _get_client_ip(request)
        path = request.url.path
        now = time.time()

        # ── Search tier (tighter) ─────────────────────────────────────────
        if path.startswith(_SEARCH_PATH_PREFIXES):
            allowed, retry_after = await self._check_limit(
                key=f"rl:search:{ip}",
                limit=self._search_limit,
                window=_SEARCH_WINDOW,
                now=now,
            )
            if not allowed:
                return self._too_many(retry_after, tier="search")

        # ── Global tier ───────────────────────────────────────────────────
        allowed, retry_after = await self._check_limit(
            key=f"rl:global:{ip}",
            limit=self._global_limit,
            window=float(_GLOBAL_WINDOW),
            now=now,
        )
        if not allowed:
            return self._too_many(retry_after, tier="global")

        response = await call_next(request)

        # Expose rate-limit info in response headers
        response.headers["X-RateLimit-Policy"] = (
            f"{self._global_limit};w={_GLOBAL_WINDOW} "
            f"{self._search_limit};w={int(_SEARCH_WINDOW)}"
        )
        return response

    # -----------------------------------------------------------------------
    # Sliding-window logic
    # -----------------------------------------------------------------------

    async def _check_limit(
        self,
        key: str,
        limit: int,
        window: float,
        now: float,
    ) -> tuple[bool, float]:
        """Apply sliding-window rate limit using a Redis Sorted Set.

        Returns
        -------
        tuple[bool, float]
            (is_allowed, retry_after_seconds)
        """
        window_start = now - window
        request_id = str(uuid.uuid4())

        pipe = self._redis.pipeline()
        # 1. Remove expired members
        pipe.zremrangebyscore(key, "-inf", window_start)
        # 2. Count current window members
        pipe.zcard(key)
        # 3. Add current request
        pipe.zadd(key, {request_id: now})
        # 4. Reset TTL to prevent orphaned keys
        pipe.expire(key, int(window * 2) + 1)
        results = await pipe.execute()

        current_count: int = int(results[1])  # count BEFORE adding current req

        if current_count >= limit:
            # Remove the request we just added (we're rejecting it)
            await self._redis.zrem(key, request_id)
            retry_after = window - (now - window_start)
            return False, max(0.0, retry_after)

        return True, 0.0

    # -----------------------------------------------------------------------
    # 429 response factory
    # -----------------------------------------------------------------------

    @staticmethod
    def _too_many(retry_after: float, tier: str) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too Many Requests",
                "tier": tier,
                "retry_after_seconds": round(retry_after, 2),
            },
            headers={
                "Retry-After": str(int(retry_after) + 1),
                "X-RateLimit-Tier": tier,
            },
        )
