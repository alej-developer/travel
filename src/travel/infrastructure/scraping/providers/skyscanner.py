"""Skyscanner scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class SkyscannerScraper(BaseScraper):
    """Scrapes flights from skyscanner.es — flight metasearch engine."""

    domain = "skyscanner.es"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        dep_date = request.departure_date.replace("-", "")  # YYYYMMDD
        url = (
            f"https://www.skyscanner.es/transporte/vuelos/{request.origin.lower()}"
            f"/{request.destination.lower()}/{dep_date[2:]}"
            f"/?adults={request.adults}&adultsv2={request.adults}"
        )

        logger.info("[SkyscannerScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=35_000)

            # Accept cookies
            try:
                await page.click('#acceptCookieButton, #onetrust-accept-btn-handler', timeout=5_000)
            except Exception:
                pass

            # Skyscanner takes time to load results
            await page.wait_for_selector(
                '[class*="FlightsResults"], .day-list-item', timeout=35_000
            )

            cards = await page.query_selector_all(
                '[class*="FlightsResults"] [class*="UpperTicketBody"], .day-list-item'
            )
            for card in cards:
                try:
                    dep_el = await card.query_selector('[class*="depart"], .departure')
                    arr_el = await card.query_selector('[class*="arrive"], .arrival')
                    price_el = await card.query_selector('[class*="price"], .price')
                    airline_el = await card.query_selector('[class*="carrier"], .airline')
                    duration_el = await card.query_selector('[class*="duration"], .duration')
                    stops_el = await card.query_selector('[class*="stops"], .stops')

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "airline": await airline_el.inner_text() if airline_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "stops": await stops_el.inner_text() if stops_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[SkyscannerScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
