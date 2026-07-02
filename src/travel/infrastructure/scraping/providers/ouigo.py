"""Ouigo España scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class OuigoScraper(BaseScraper):
    """Scrapes low-cost AVE trains from ouigo.com — SNCF's low-cost Spain service."""

    domain = "ouigo.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.ouigo.com/es/search"
            f"?origin={request.origin}"
            f"&destination={request.destination}"
            f"&date={request.departure_date}"
            f"&passengers={request.adults}"
        )

        logger.info("[OuigoScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('.cookie-consent-accept, #accept-cookies', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector('.journey-card, .trip-result', timeout=25_000)

            cards = await page.query_selector_all('.journey-card, .trip-result')
            for card in cards:
                try:
                    dep_el = await card.query_selector('.departure, .dep-time')
                    arr_el = await card.query_selector('.arrival, .arr-time')
                    price_el = await card.query_selector('.price, .fare-price')
                    duration_el = await card.query_selector('.duration, .trip-duration')

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[OuigoScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
