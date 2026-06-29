"""Renfe scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class RenfeScraper(BaseScraper):
    """Scrapes train journeys from renfe.com."""

    domain = "renfe.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = "https://www.renfe.com/es/es/viajar/es-facil-viajar/billetes-y-ofertas/buscar-billetes"

        logger.info("[RenfeScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Fill origin
            await page.fill('#origin', request.origin, timeout=10_000)
            await page.wait_for_selector('.autocomplete-item', timeout=5_000)
            await page.click('.autocomplete-item:first-child')

            # Fill destination
            await page.fill('#destination', request.destination)
            await page.wait_for_selector('.autocomplete-item', timeout=5_000)
            await page.click('.autocomplete-item:first-child')

            # Fill departure date
            await page.fill('[name="dateOutward"]', request.departure_date)

            # Submit
            await page.click('[id="search-submit"]')
            await page.wait_for_selector('.train-row', timeout=30_000)

            rows = await page.query_selector_all('.train-row')
            for row in rows:
                try:
                    dep_el = await row.query_selector('.departure-time')
                    arr_el = await row.query_selector('.arrival-time')
                    price_el = await row.query_selector('.price')
                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Row parse error: {exc}")

        except Exception as exc:
            logger.exception("[RenfeScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
