"""Airbnb scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    """Scrapes accommodation offers from airbnb.com."""

    domain = "airbnb.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.airbnb.com/s/{request.destination}/homes"
            f"?checkin={request.departure_date}"
            f"&checkout={request.return_date or ''}"
            f"&adults={request.adults}"
        )

        logger.info("[AirbnbScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Airbnb renders listing cards server-side; wait for them
            await page.wait_for_selector('[data-testid="listing-card-title"]', timeout=25_000)

            title_els = await page.query_selector_all('[data-testid="listing-card-title"]')
            price_els = await page.query_selector_all('[data-testid="price-availability-row"]')

            for i, title_el in enumerate(title_els):
                try:
                    price_el = price_els[i] if i < len(price_els) else None
                    raw_items.append({
                        "name": await title_el.inner_text(),
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Listing parse error: {exc}")

        except Exception as exc:
            logger.exception("[AirbnbScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
