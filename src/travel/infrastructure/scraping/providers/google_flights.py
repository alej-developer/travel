"""Google Flights scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class GoogleFlightsScraper(BaseScraper):
    """Scrapes flights from Google Flights — Google's flight metasearch."""

    domain = "google.com/travel/flights"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.google.com/travel/flights/search"
            f"?tfs=CBwQAhopEgoyMDI2LTA3LTEwagwIAhIIL20vMGY4dDlyDAgCEggvbS8wNnFkNAAaKRIKMjAyNi0wNy0xN2oMCAISCC9tLzA2cWQ5cgwIAhIIL20vMGY4dDlAAUgBcAGCAQsI____________AZgBAQ"
        )
        # For Google Flights, we construct a simplified direct URL
        simple_url = (
            f"https://www.google.com/travel/flights?q=flights"
            f"+from+{request.origin}+to+{request.destination}"
            f"+on+{request.departure_date}"
        )

        logger.info("[GoogleFlightsScraper] GET %s", simple_url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(simple_url, wait_until="domcontentloaded", timeout=35_000)

            # Accept cookies
            try:
                await page.click(
                    '[aria-label="Accept all"], button:has-text("Aceptar todo")',
                    timeout=5_000,
                )
            except Exception:
                pass

            # Wait for flight results
            await page.wait_for_selector(
                '[class*="pIav2d"], [data-resultid], .gws-flights-results__result-item',
                timeout=35_000,
            )

            cards = await page.query_selector_all(
                '[data-resultid], [class*="pIav2d"], .gws-flights-results__result-item'
            )
            for card in cards:
                try:
                    dep_el = await card.query_selector(
                        '[class*="wtdjmc"], [aria-label*="Departure"], .departure'
                    )
                    arr_el = await card.query_selector(
                        '[class*="XWcVob"], [aria-label*="Arrival"], .arrival'
                    )
                    price_el = await card.query_selector(
                        '[class*="price"], [class*="YMlIz"]'
                    )
                    airline_el = await card.query_selector(
                        '[class*="Ir0Voe"], .airline-name'
                    )
                    duration_el = await card.query_selector(
                        '[class*="Ak5kof"], .duration'
                    )
                    stops_el = await card.query_selector(
                        '[class*="EfT7Ae"], .stops'
                    )

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
            logger.exception("[GoogleFlightsScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
