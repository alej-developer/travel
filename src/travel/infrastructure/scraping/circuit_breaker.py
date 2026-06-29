"""Circuit Breaker backed by Redis.

Architecture
------------
Each provider domain gets its own Redis key namespace::

    circuit:<domain>:failures   INT  — consecutive 429 count
    circuit:<domain>:open_until FLOAT — unix timestamp when circuit closes again

State machine
-------------
  CLOSED  → normal operation
  OPEN    → domain tripped, all calls rejected until open_until expires
  (no HALF-OPEN in this implementation — we re-close automatically at expiry)

Usage
-----
    cb = CircuitBreaker(redis_client, domain="booking.com")

    if await cb.is_open():
        raise CircuitOpenError("booking.com is paused")

    try:
        result = await scrape_something()
        await cb.record_success()
    except RateLimitError:
        await cb.record_failure()
        raise
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Final

import redis.asyncio as aioredis

from travel.config import get_settings

# Redis key templates
_KEY_FAILURES: Final[str] = "circuit:{domain}:failures"
_KEY_OPEN_UNTIL: Final[str] = "circuit:{domain}:open_until"


class CircuitOpenError(Exception):
    """Raised when a request is made to an open (tripped) circuit."""

    def __init__(self, domain: str, retry_after: float) -> None:
        self.domain = domain
        self.retry_after = retry_after
        remaining = max(0.0, retry_after - time.time())
        super().__init__(
            f"Circuit OPEN for '{domain}'. "
            f"Retry in {remaining:.0f}s."
        )


@dataclass
class CircuitBreakerState:
    """Snapshot of the circuit state for a given domain."""

    domain: str
    failures: int
    is_open: bool
    open_until: float | None  # unix timestamp, None when closed


class CircuitBreaker:
    """Per-domain async circuit breaker backed by Redis.

    Parameters
    ----------
    redis_client:
        An ``redis.asyncio.Redis`` instance (or compatible).
    domain:
        The provider domain string used as the Redis key discriminator.
        E.g. ``"booking.com"``, ``"iberia.com"``.
    threshold:
        Number of consecutive 429 failures that trip the circuit.
    timeout_seconds:
        Duration (seconds) for which the circuit stays open after tripping.
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,  # type: ignore[type-arg]
        domain: str,
        threshold: int | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self._redis = redis_client
        self.domain = domain
        cfg = get_settings()
        self._threshold: int = threshold if threshold is not None else cfg.circuit_breaker_threshold
        self._timeout: int = (
            timeout_seconds if timeout_seconds is not None else cfg.circuit_breaker_timeout_seconds
        )

    # -----------------------------------------------------------------------
    # Redis key helpers
    # -----------------------------------------------------------------------

    @property
    def _failures_key(self) -> str:
        return _KEY_FAILURES.format(domain=self.domain)

    @property
    def _open_until_key(self) -> str:
        return _KEY_OPEN_UNTIL.format(domain=self.domain)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def is_open(self) -> bool:
        """Return True if the circuit is currently open (domain paused)."""
        raw = await self._redis.get(self._open_until_key)
        if raw is None:
            return False
        open_until = float(raw)
        if time.time() < open_until:
            return True
        # Circuit expired — auto-reset
        await self._reset()
        return False

    async def guard(self) -> None:
        """Raise CircuitOpenError if the circuit is open."""
        raw = await self._redis.get(self._open_until_key)
        if raw is not None:
            open_until = float(raw)
            if time.time() < open_until:
                raise CircuitOpenError(self.domain, open_until)
            await self._reset()

    async def record_failure(self) -> int:
        """Increment consecutive failure counter; trip circuit if threshold met.

        Returns
        -------
        int
            Current failure count after incrementing.
        """
        failures = await self._redis.incr(self._failures_key)
        # Set TTL on the failures key so it auto-expires even if never reset
        await self._redis.expire(self._failures_key, self._timeout * 2)

        if failures >= self._threshold:
            open_until = time.time() + self._timeout
            await self._redis.set(self._open_until_key, open_until, ex=self._timeout)

        return int(failures)

    async def record_success(self) -> None:
        """Reset failure counter on a successful scrape."""
        await self._reset()

    async def get_state(self) -> CircuitBreakerState:
        """Return a snapshot of the current circuit state."""
        failures_raw, open_until_raw = await self._redis.mget(
            self._failures_key, self._open_until_key
        )
        failures = int(failures_raw) if failures_raw else 0
        open_until: float | None = float(open_until_raw) if open_until_raw else None
        is_open = open_until is not None and time.time() < open_until
        return CircuitBreakerState(
            domain=self.domain,
            failures=failures,
            is_open=is_open,
            open_until=open_until,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _reset(self) -> None:
        """Delete both Redis keys, returning circuit to CLOSED state."""
        await self._redis.delete(self._failures_key, self._open_until_key)
