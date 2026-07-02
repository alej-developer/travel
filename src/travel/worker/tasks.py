"""Celery tasks for the distributed scraping engine.

Task hierarchy
--------------
``scrape_provider``  (leaf task)
    Runs a single provider scrape for a given ScrapeRequest.
    • Checks circuit breaker before starting.
    • Creates a Playwright session with a fresh fingerprint and a rotated proxy.
    • Installs the network middleware (resource blocking + 429 detection).
    • On 429: records circuit-breaker failure, rotates proxy, retries up to 3×.
    • On success: records circuit-breaker success, persists raw results.

``scrape_all_providers``  (fan-out task)
    Sends one ``scrape_provider`` sub-task per registered domain and returns
    a Celery group result.

Retry policy
------------
We use :func:`tenacity` inside the task for fine-grained retry logic (proxy
rotation on each attempt), while Celery's built-in ``retry`` handles
unrecoverable errors (circuit open, fatal exceptions).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import redis.asyncio as aioredis
from celery import group
from playwright.async_api import async_playwright
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from travel.config import get_settings
from travel.infrastructure.scraping.base_scraper import ScrapeRequest, ScrapeResult
from travel.infrastructure.scraping.circuit_breaker import CircuitBreaker, CircuitOpenError
from travel.infrastructure.scraping.network_middleware import NetworkMiddleware
from travel.infrastructure.scraping.proxy_pool import ProxyPool
from travel.infrastructure.scraping.scraper_factory import ScraperFactory, UnknownProviderError
from travel.infrastructure.scraping.session_manager import SessionManager
from travel.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared singletons (per-process, created lazily)
# ---------------------------------------------------------------------------

_proxy_pool: ProxyPool | None = None


def _get_proxy_pool() -> ProxyPool:
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ProxyPool.from_settings()
    return _proxy_pool


def _build_redis_client() -> aioredis.Redis:  # type: ignore[type-arg]
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


# ---------------------------------------------------------------------------
# Async scrape runner (runs inside asyncio.run() from Celery task)
# ---------------------------------------------------------------------------

class _RateLimitError(Exception):
    """Internal signal: 429 detected during page load."""


async def _run_scrape(
    domain: str,
    request: ScrapeRequest,
    proxy: str | None,
) -> ScrapeResult:
    """Execute a single scrape inside an async context.

    Raises _RateLimitError if a 429 is detected by the network middleware.
    """
    scraper = ScraperFactory.create(domain)
    rate_limited: bool = False

    async def on_rate_limit(url: str) -> None:
        nonlocal rate_limited
        rate_limited = True

    async with async_playwright() as pw:
        async with SessionManager(pw, proxy=proxy) as session:
            page = await session.new_page()
            middleware = NetworkMiddleware(page, on_rate_limit=on_rate_limit)
            await middleware.install()

            result = await scraper.scrape(page, request)

    if rate_limited:
        raise _RateLimitError(f"429 detected while scraping {domain}")

    return result


# ---------------------------------------------------------------------------
# Celery task: scrape a single provider
# ---------------------------------------------------------------------------

@celery_app.task(
    name="travel.worker.tasks.scrape_provider",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="10/m",          # max 10 executions per minute per worker
    acks_late=True,
    time_limit=120,             # hard kill after 2 minutes
    soft_time_limit=100,        # soft kill (raises SoftTimeLimitExceeded)
    throws=(CircuitOpenError,),
)
def scrape_provider(
    self: Any,
    domain: str,
    request_dict: dict[str, Any],
) -> dict[str, Any]:
    """Scrape a single provider and return the raw result dict.

    Parameters
    ----------
    domain:
        Provider domain key (e.g. ``"booking.com"``).
    request_dict:
        JSON-serialisable dict matching :class:`ScrapeRequest` fields.

    Returns
    -------
    dict
        JSON-serialisable dict matching :class:`ScrapeResult` fields.
    """
    request = ScrapeRequest(**request_dict)
    settings = get_settings()
    proxy_pool = _get_proxy_pool()

    # ── Circuit breaker check ───────────────────────────────────────────────
    async def _check_and_run() -> ScrapeResult:
        redis_client = _build_redis_client()
        cb = CircuitBreaker(redis_client, domain)

        try:
            await cb.guard()  # raises CircuitOpenError if open
        except CircuitOpenError:
            await redis_client.aclose()
            raise

        # ── Retry with proxy rotation ───────────────────────────────────────
        proxy = proxy_pool.next_proxy()
        attempts = 0

        while attempts < settings.circuit_breaker_threshold:
            try:
                result = await _run_scrape(domain, request, proxy)
                await cb.record_success()
                if proxy:
                    proxy_pool.mark_success(proxy)
                await redis_client.aclose()
                return result

            except _RateLimitError:
                attempts += 1
                failure_count = await cb.record_failure()
                logger.warning(
                    "[%s] 429 detected. Failure count=%d/%d. Rotating proxy.",
                    domain, failure_count, settings.circuit_breaker_threshold,
                )
                if proxy:
                    proxy_pool.mark_failed(proxy)
                proxy = proxy_pool.next_proxy()

                if failure_count >= settings.circuit_breaker_threshold:
                    logger.error(
                        "[%s] Circuit TRIPPED. Paused for %ds.",
                        domain, settings.circuit_breaker_timeout_seconds,
                    )
                    await redis_client.aclose()
                    raise CircuitOpenError(domain, 0)

            except Exception as exc:
                logger.exception("[%s] Unexpected error", domain)
                await redis_client.aclose()
                raise

        # All retries exhausted
        await redis_client.aclose()
        raise _RateLimitError(f"All retry attempts exhausted for {domain}")

    try:
        result = asyncio.run(_check_and_run())
        return {
            "provider": result.provider,
            "raw_items": result.raw_items,
            "errors": result.errors,
            "was_rate_limited": result.was_rate_limited,
        }

    except CircuitOpenError as exc:
        # Don't retry — circuit is open, let it heal
        logger.warning("[%s] Circuit open — not retrying this task.", domain)
        raise

    except UnknownProviderError:
        logger.error("[%s] No scraper registered — will not retry.", domain)
        raise

    except Exception as exc:
        logger.exception("[%s] Retrying task due to error: %s", domain, exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Celery task: fan-out to all providers
# ---------------------------------------------------------------------------

@celery_app.task(
    name="travel.worker.tasks.scrape_all_providers",
    acks_late=True,
)
def scrape_all_providers(request_dict: dict[str, Any]) -> Any:
    """Fan out a scrape request to all registered provider domains.

    Returns a Celery GroupResult whose individual results are ScrapeResult dicts.
    """
    domains = ScraperFactory.available_domains()
    logger.info("Fanning out scrape to %d providers: %s", len(domains), domains)

    job = group(
        scrape_provider.s(domain, request_dict)
        for domain in domains
    )
    return job.apply_async()


# ---------------------------------------------------------------------------
# Celery task: fan-out to providers filtered by transport type
# ---------------------------------------------------------------------------

@celery_app.task(
    name="travel.worker.tasks.scrape_by_type",
    acks_late=True,
)
def scrape_by_type(transport_type: str, request_dict: dict[str, Any]) -> Any:
    """Fan out a scrape request only to providers matching the transport type.

    Parameters
    ----------
    transport_type:
        One of ``"train"``, ``"flight"``, or ``"accommodation"``.
    request_dict:
        JSON-serialisable dict matching :class:`ScrapeRequest` fields.

    Returns
    -------
    GroupResult
        Celery group result with one sub-task per matched provider.
    """
    domains = ScraperFactory.for_transport_type(transport_type)
    logger.info(
        "Fanning out %s scrape to %d providers: %s",
        transport_type, len(domains), domains,
    )

    if not domains:
        logger.warning("No providers registered for transport type %r", transport_type)
        return None

    job = group(
        scrape_provider.s(domain, request_dict)
        for domain in domains
    )
    return job.apply_async()

