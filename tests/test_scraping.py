"""Scraping engine smoke tests.

Tests are fully in-memory — no Redis, no Playwright browser, no network.
All external I/O is mocked.

Coverage
--------
1. ScraperFactory — registration, creation, from_url, unknown domain error.
2. BrowserFingerprint — randomness, coherence, viewport computation.
3. ProxyPool — round-robin rotation, failure tracking, ban window.
4. CircuitBreaker — record_failure, threshold trip, is_open, auto-reset via mock.
5. NetworkMiddleware — resource blocking route handler, 429 callback.
6. Celery app — app is importable and configured correctly.
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. ScraperFactory
# ---------------------------------------------------------------------------


class TestScraperFactory:
    def test_create_known_domain(self) -> None:
        from travel.infrastructure.scraping.scraper_factory import ScraperFactory

        scraper = ScraperFactory.create("booking.com")
        assert scraper.domain == "booking.com"

    def test_create_returns_same_instance(self) -> None:
        from travel.infrastructure.scraping.scraper_factory import ScraperFactory

        a = ScraperFactory.create("airbnb.com")
        b = ScraperFactory.create("airbnb.com")
        assert a is b

    def test_from_url_booking(self) -> None:
        from travel.infrastructure.scraping.scraper_factory import ScraperFactory

        s = ScraperFactory.from_url("https://www.booking.com/searchresults.html?ss=Madrid")
        assert s.domain == "booking.com"

    def test_from_url_iberia(self) -> None:
        from travel.infrastructure.scraping.scraper_factory import ScraperFactory

        s = ScraperFactory.from_url("https://www.iberia.com/vuelos-baratos/mad-bcn/")
        assert s.domain == "iberia.com"

    def test_unknown_domain_raises(self) -> None:
        from travel.infrastructure.scraping.scraper_factory import (
            ScraperFactory,
            UnknownProviderError,
        )

        with pytest.raises(UnknownProviderError, match="unknown.com"):
            ScraperFactory.create("unknown.com")

    def test_register_new_provider(self) -> None:
        from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult
        from travel.infrastructure.scraping.scraper_factory import ScraperFactory
        from playwright.async_api import Page

        class DummyScraper(BaseScraper):
            domain = "dummy.test"

            async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
                return ScrapeResult(provider=self.domain, raw_items=[])

        ScraperFactory.register("dummy.test", DummyScraper)
        s = ScraperFactory.create("dummy.test")
        assert isinstance(s, DummyScraper)

    def test_available_domains(self) -> None:
        from travel.infrastructure.scraping.scraper_factory import ScraperFactory

        domains = ScraperFactory.available_domains()
        assert "booking.com" in domains
        assert "renfe.com" in domains
        assert "iberia.com" in domains
        assert "airbnb.com" in domains
        assert domains == sorted(domains)  # must be sorted


# ---------------------------------------------------------------------------
# 2. BrowserFingerprint
# ---------------------------------------------------------------------------


class TestBrowserFingerprint:
    def test_all_fields_populated(self) -> None:
        from travel.infrastructure.scraping.session_manager import BrowserFingerprint

        fp = BrowserFingerprint()
        assert fp.user_agent
        assert fp.platform
        assert fp.locale
        assert fp.timezone_id
        assert fp.screen
        assert fp.webgl
        assert 0 <= fp.canvas_noise_seed <= 255
        assert fp.hardware_concurrency > 0
        assert fp.device_memory > 0

    def test_viewport_smaller_than_screen(self) -> None:
        from travel.infrastructure.scraping.session_manager import BrowserFingerprint

        fp = BrowserFingerprint()
        assert fp.viewport["width"] <= fp.screen["width"]
        assert fp.viewport["height"] < fp.screen["height"]

    def test_two_fingerprints_differ(self) -> None:
        from travel.infrastructure.scraping.session_manager import BrowserFingerprint

        fps = [BrowserFingerprint() for _ in range(20)]
        canvas_seeds = {fp.canvas_noise_seed for fp in fps}
        # With 20 samples from 0-255, highly unlikely all are the same
        assert len(canvas_seeds) > 1

    def test_fingerprint_script_contains_webgl(self) -> None:
        from travel.infrastructure.scraping.session_manager import (
            BrowserFingerprint,
            _build_fingerprint_script,
        )

        fp = BrowserFingerprint()
        script = _build_fingerprint_script(fp)
        assert "WebGLRenderingContext" in script
        assert fp.webgl["vendor"] in script
        assert "Canvas" in script or "toDataURL" in script


# ---------------------------------------------------------------------------
# 3. ProxyPool
# ---------------------------------------------------------------------------


class TestProxyPool:
    def test_empty_pool_returns_none(self) -> None:
        from travel.infrastructure.scraping.proxy_pool import ProxyPool

        pool = ProxyPool([])
        assert pool.next_proxy() is None

    def test_round_robin_rotation(self) -> None:
        from travel.infrastructure.scraping.proxy_pool import ProxyPool

        proxies = ["proxy1", "proxy2", "proxy3"]
        pool = ProxyPool(proxies)
        results = [pool.next_proxy() for _ in range(6)]
        # Each proxy should appear twice in 6 calls
        for p in proxies:
            assert results.count(p) == 2

    def test_ban_after_failures(self) -> None:
        from travel.infrastructure.scraping.proxy_pool import (
            ProxyPool,
            _MAX_CONSECUTIVE_FAILURES,
        )

        pool = ProxyPool(["only-proxy"])
        for _ in range(_MAX_CONSECUTIVE_FAILURES):
            pool.mark_failed("only-proxy")
        # Proxy is now banned → next_proxy returns None
        assert pool.next_proxy() is None

    def test_mark_success_resets_failures(self) -> None:
        from travel.infrastructure.scraping.proxy_pool import (
            ProxyPool,
            _MAX_CONSECUTIVE_FAILURES,
        )

        pool = ProxyPool(["p1", "p2"])
        for _ in range(_MAX_CONSECUTIVE_FAILURES - 1):
            pool.mark_failed("p1")
        pool.mark_success("p1")
        # After success, failure count should be 0 — p1 should still be available
        assert pool._stats["p1"].consecutive_failures == 0

    def test_available_count(self) -> None:
        from travel.infrastructure.scraping.proxy_pool import (
            ProxyPool,
            _MAX_CONSECUTIVE_FAILURES,
        )

        pool = ProxyPool(["p1", "p2", "p3"])
        assert pool.available == 3
        for _ in range(_MAX_CONSECUTIVE_FAILURES):
            pool.mark_failed("p1")
        assert pool.available == 2


# ---------------------------------------------------------------------------
# 4. CircuitBreaker (Redis mocked)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_redis() -> AsyncMock:
    """Return a fully-mocked async Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.mget = AsyncMock(return_value=[None, None])
    return redis


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_closed_when_no_failures(self, mock_redis: AsyncMock) -> None:
        from travel.infrastructure.scraping.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(mock_redis, "booking.com", threshold=3, timeout_seconds=900)
        mock_redis.get.return_value = None
        assert not await cb.is_open()

    @pytest.mark.asyncio
    async def test_opens_at_threshold(self, mock_redis: AsyncMock) -> None:
        from travel.infrastructure.scraping.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(mock_redis, "booking.com", threshold=3, timeout_seconds=900)
        mock_redis.incr.return_value = 3  # hits threshold
        count = await cb.record_failure()
        assert count == 3
        # Should have called redis.set to store open_until
        mock_redis.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_guard_raises_when_open(self, mock_redis: AsyncMock) -> None:
        from travel.infrastructure.scraping.circuit_breaker import (
            CircuitBreaker,
            CircuitOpenError,
        )

        cb = CircuitBreaker(mock_redis, "booking.com", threshold=3, timeout_seconds=900)
        # Simulate open circuit: open_until is far in the future
        mock_redis.get.return_value = str(time.time() + 9999)
        with pytest.raises(CircuitOpenError, match="booking.com"):
            await cb.guard()

    @pytest.mark.asyncio
    async def test_auto_reset_when_expired(self, mock_redis: AsyncMock) -> None:
        from travel.infrastructure.scraping.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(mock_redis, "booking.com", threshold=3, timeout_seconds=900)
        # open_until is in the past
        mock_redis.get.return_value = str(time.time() - 1)
        result = await cb.is_open()
        assert not result
        # Should have called delete to reset
        mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_record_success_resets(self, mock_redis: AsyncMock) -> None:
        from travel.infrastructure.scraping.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(mock_redis, "booking.com", threshold=3, timeout_seconds=900)
        await cb.record_success()
        mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_state_returns_snapshot(self, mock_redis: AsyncMock) -> None:
        from travel.infrastructure.scraping.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(mock_redis, "booking.com", threshold=3, timeout_seconds=900)
        mock_redis.mget.return_value = [b"2", None]
        state = await cb.get_state()
        assert state.domain == "booking.com"
        assert state.failures == 2
        assert not state.is_open


# ---------------------------------------------------------------------------
# 5. NetworkMiddleware
# ---------------------------------------------------------------------------


class TestNetworkMiddleware:
    @pytest.mark.asyncio
    async def test_blocks_image_resources(self) -> None:
        from travel.infrastructure.scraping.network_middleware import NetworkMiddleware

        page = MagicMock()
        page.route = AsyncMock()
        page.on = MagicMock()
        middleware = NetworkMiddleware(page)
        await middleware.install()

        page.route.assert_awaited_once_with("**/*", middleware._handle_route)

    @pytest.mark.asyncio
    async def test_route_aborts_image(self) -> None:
        from travel.infrastructure.scraping.network_middleware import NetworkMiddleware

        page = MagicMock()
        page.route = AsyncMock()
        page.on = MagicMock()

        middleware = NetworkMiddleware(page)

        route = AsyncMock()
        request = MagicMock()
        request.resource_type = "image"
        request.url = "https://example.com/photo.jpg"

        await middleware._handle_route(route, request)
        route.abort.assert_awaited_once_with("blockedbyclient")
        route.continue_.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_route_blocks_tracker_url(self) -> None:
        from travel.infrastructure.scraping.network_middleware import NetworkMiddleware

        page = MagicMock()
        page.route = AsyncMock()
        page.on = MagicMock()

        middleware = NetworkMiddleware(page)

        route = AsyncMock()
        request = MagicMock()
        request.resource_type = "script"
        request.url = "https://www.google-analytics.com/analytics.js"

        await middleware._handle_route(route, request)
        route.abort.assert_awaited_once_with("blockedbyclient")

    @pytest.mark.asyncio
    async def test_route_allows_document(self) -> None:
        from travel.infrastructure.scraping.network_middleware import NetworkMiddleware

        page = MagicMock()
        page.route = AsyncMock()
        page.on = MagicMock()

        middleware = NetworkMiddleware(page)

        route = AsyncMock()
        request = MagicMock()
        request.resource_type = "document"
        request.url = "https://www.booking.com/searchresults.html"

        await middleware._handle_route(route, request)
        route.continue_.assert_awaited_once()
        route.abort.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rate_limit_callback_triggered(self) -> None:
        from travel.infrastructure.scraping.network_middleware import NetworkMiddleware

        page = MagicMock()
        page.route = AsyncMock()
        page.on = MagicMock()

        triggered: list[str] = []

        async def on_rl(url: str) -> None:
            triggered.append(url)

        middleware = NetworkMiddleware(page, on_rate_limit=on_rl)

        # Simulate a 429 response
        response = MagicMock()
        response.status = 429
        response.url = "https://www.booking.com/searchresults.html"

        await middleware._handle_response(response)
        assert middleware.was_rate_limited()
        assert triggered == ["https://www.booking.com/searchresults.html"]


# ---------------------------------------------------------------------------
# 6. Celery app configuration
# ---------------------------------------------------------------------------


class TestCeleryApp:
    def test_app_importable(self) -> None:
        from travel.worker.celery_app import celery_app  # noqa: F401

    def test_app_name(self) -> None:
        from travel.worker.celery_app import celery_app

        assert celery_app.main == "travel"

    def test_task_serializer_is_json(self) -> None:
        from travel.worker.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"

    def test_acks_late_enabled(self) -> None:
        from travel.worker.celery_app import celery_app

        assert celery_app.conf.task_acks_late is True

    def test_scrape_provider_task_registered(self) -> None:
        # tasks module must be imported for tasks to register on the app
        import travel.worker.tasks  # noqa: F401
        from travel.worker.celery_app import celery_app

        assert "travel.worker.tasks.scrape_provider" in celery_app.tasks

    def test_scrape_all_providers_task_registered(self) -> None:
        import travel.worker.tasks  # noqa: F401
        from travel.worker.celery_app import celery_app

        assert "travel.worker.tasks.scrape_all_providers" in celery_app.tasks
