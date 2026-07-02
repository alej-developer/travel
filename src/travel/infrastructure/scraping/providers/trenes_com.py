"""Trenes.com scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class TrenesComScraper(BaseScraper):
    """Scrapes train tickets from trenes.com — Spanish train comparator."""

    domain = "trenes.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.trenes.com/search"
            f"?origin={request.origin}"
            f"&destination={request.destination}"
            f"&departure={request.departure_date}"
            f"&adults={request.adults}"
        )

        logger.info("[TrenesComScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies if present
            try:
                await page.click('[id="cookiesAccept"], .cookie-accept', timeout=4_000)
            except Exception:
                pass

            # Wait for result cards
            await page.wait_for_selector('.search-result, .trip-card', timeout=25_000)

            cards = await page.query_selector_all('.search-result, .trip-card')
            for card in cards:
                try:
                    dep_el = await card.query_selector('.departure-time, .time-dep')
                    arr_el = await card.query_selector('.arrival-time, .time-arr')
                    price_el = await card.query_selector('.price, .amount')
                    operator_el = await card.query_selector('.operator, .train-operator')
                    duration_el = await card.query_selector('.duration, .trip-duration')

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "operator": await operator_el.inner_text() if operator_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[TrenesComScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
