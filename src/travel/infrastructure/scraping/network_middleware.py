"""Network middleware for Playwright pages.

Responsibilities
----------------
1. **Resource blocking** — intercepts all network requests and aborts
   image and font loading to save bandwidth (critical in distributed scraping).
2. **Proxy rotation** — on every ``route`` call it checks if the underlying
   request returned a 429; if so it signals the caller to swap the proxy.

Because Playwright's routing API is synchronous-callback-based, the
``NetworkMiddleware`` wraps it in a clean async-friendly interface.

Usage
-----
    middleware = NetworkMiddleware(page)
    await middleware.install()          # attaches request interceptor
    # ... page.goto(...) ...
    # In case of 429 detection, middleware fires on_rate_limit callback.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Final

from playwright.async_api import Page, Request, Route

logger = logging.getLogger(__name__)

# Resource types to block outright
_BLOCKED_RESOURCE_TYPES: Final[frozenset[str]] = frozenset(
    {"image", "media", "font", "stylesheet"}
)

# Domains whose responses are never needed (analytics, ads)
_BLOCKED_URL_FRAGMENTS: Final[tuple[str, ...]] = (
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "facebook.com/tr",
    "hotjar.com",
    "criteo.com",
    "adnxs.com",
    "amazon-adsystem.com",
)

RateLimitCallback = Callable[[str], Awaitable[None]]


class NetworkMiddleware:
    """Playwright network middleware: blocks waste and detects 429s.

    Parameters
    ----------
    page:
        The Playwright ``Page`` instance to instrument.
    on_rate_limit:
        Async callback invoked with the URL string whenever a 429 response
        is detected. The caller should record a circuit-breaker failure there.
    """

    def __init__(
        self,
        page: Page,
        on_rate_limit: RateLimitCallback | None = None,
    ) -> None:
        self._page = page
        self._on_rate_limit = on_rate_limit
        self._rate_limit_event = asyncio.Event()

    async def install(self) -> None:
        """Attach routing and response listeners to the page."""
        # Route handler: blocks unwanted resource types / domains
        await self._page.route("**/*", self._handle_route)
        # Response listener: detects 429 on remaining responses
        self._page.on("response", self._handle_response)

    # -----------------------------------------------------------------------
    # Route handler
    # -----------------------------------------------------------------------

    async def _handle_route(self, route: Route, request: Request) -> None:
        """Abort blocked resource types; continue everything else."""
        resource_type = request.resource_type
        url = request.url

        # Block by resource type
        if resource_type in _BLOCKED_RESOURCE_TYPES:
            await route.abort("blockedbyclient")
            return

        # Block by URL fragment (trackers / analytics)
        if any(frag in url for frag in _BLOCKED_URL_FRAGMENTS):
            await route.abort("blockedbyclient")
            return

        await route.continue_()

    # -----------------------------------------------------------------------
    # Response listener
    # -----------------------------------------------------------------------

    async def _handle_response(self, response: object) -> None:
        """Detect 429 responses and fire the rate-limit callback."""
        from playwright.async_api import Response  # local import to avoid circular

        resp: Response = response  # type: ignore[assignment]
        if resp.status == 429:
            url = resp.url
            logger.warning("429 Too Many Requests detected: %s", url)
            self._rate_limit_event.set()
            if self._on_rate_limit:
                try:
                    await self._on_rate_limit(url)
                except Exception:
                    logger.exception("Error in on_rate_limit callback for %s", url)

    def was_rate_limited(self) -> bool:
        """Return True if a 429 was seen since last reset."""
        return self._rate_limit_event.is_set()

    def reset_rate_limit_flag(self) -> None:
        """Clear the rate-limit flag (call after proxy rotation)."""
        self._rate_limit_event.clear()
