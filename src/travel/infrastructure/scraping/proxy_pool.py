"""Residential proxy pool with round-robin rotation and failure tracking.

Architecture
------------
Proxies are loaded from ``Settings.proxy_urls``. The pool exposes:

- ``next_proxy()``  — returns the next proxy in a round-robin fashion.
- ``mark_failed(proxy)`` — increments failure counter; after N failures
  the proxy is temporarily removed from rotation (ban window).
- ``mark_success(proxy)`` — resets failure counter.

The pool is intentionally **in-process** (no Redis) to keep rotation
sub-millisecond. If a cluster-wide shared pool is needed later, the
interface can be backed by Redis Sorted Sets.

Usage
-----
    pool = ProxyPool.from_settings()
    proxy = pool.next_proxy()          # may return None if list is empty

    try:
        result = await scrape(proxy)
        pool.mark_success(proxy)
    except RateLimitError:
        proxy = pool.next_proxy()      # rotate immediately
"""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Final

from travel.config import get_settings

logger = logging.getLogger(__name__)

_MAX_CONSECUTIVE_FAILURES: Final[int] = 5
_BAN_WINDOW_SECONDS: Final[float] = 300.0  # 5 min local proxy ban


@dataclass
class _ProxyStats:
    consecutive_failures: int = 0
    banned_until: float = 0.0


class ProxyPool:
    """Thread-safe, round-robin proxy pool with per-proxy ban windows.

    Parameters
    ----------
    proxies:
        List of proxy URL strings.  May be empty — in that case
        ``next_proxy()`` always returns ``None`` (direct connection).
    """

    def __init__(self, proxies: list[str]) -> None:
        self._proxies: list[str] = list(proxies)
        self._index: int = 0
        self._stats: dict[str, _ProxyStats] = defaultdict(lambda: _ProxyStats())
        self._lock = threading.Lock()

    # -----------------------------------------------------------------------
    # Factory
    # -----------------------------------------------------------------------

    @classmethod
    def from_settings(cls) -> "ProxyPool":
        """Construct pool from application settings."""
        settings = get_settings()
        proxies = settings.proxy_urls
        if not proxies:
            logger.warning(
                "ProxyPool: no proxies configured — all requests will be direct."
            )
        return cls(proxies)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def next_proxy(self) -> str | None:
        """Return the next available proxy, skipping banned ones.

        Returns ``None`` if no proxies are configured or all are banned.
        """
        if not self._proxies:
            return None

        with self._lock:
            now = time.monotonic()
            # Try each proxy once; if all banned return None
            for _ in range(len(self._proxies)):
                proxy = self._proxies[self._index % len(self._proxies)]
                self._index += 1
                stats = self._stats[proxy]
                if stats.banned_until <= now:
                    return proxy
            return None

    def mark_failed(self, proxy: str) -> None:
        """Record a failure for *proxy*; ban it locally if threshold exceeded."""
        with self._lock:
            stats = self._stats[proxy]
            stats.consecutive_failures += 1
            if stats.consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                stats.banned_until = time.monotonic() + _BAN_WINDOW_SECONDS
                logger.warning(
                    "Proxy %s banned for %.0fs after %d consecutive failures",
                    proxy,
                    _BAN_WINDOW_SECONDS,
                    stats.consecutive_failures,
                )

    def mark_success(self, proxy: str) -> None:
        """Reset failure counter for *proxy* after a successful request."""
        with self._lock:
            self._stats[proxy] = _ProxyStats()

    @property
    def size(self) -> int:
        """Total number of proxies in the pool (including banned)."""
        return len(self._proxies)

    @property
    def available(self) -> int:
        """Number of proxies currently not banned."""
        now = time.monotonic()
        return sum(
            1 for p in self._proxies if self._stats[p].banned_until <= now
        )
