"""Vueling scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class VuelingScraper(BaseScraper):
    """Scrapes flights from vueling.com — Spanish low-cost carrier (IAG group)."""

    domain = "vueling.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.vueling.com/es/reserva/select"
            f"?orig={request.origin}"
            f"&dest={request.destination}"
            f"&date={request.departure_date}"
            f"&adt={request.adults}"
        )

        logger.info("[VuelingScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('#onetrust-accept-btn-handler', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector('.flight-card, .flight-row', timeout=30_000)

            cards = await page.query_selector_all('.flight-card, .flight-row')
            for card in cards:
                try:
                    dep_el = await card.query_selector('.departure-time, .dep')
                    arr_el = await card.query_selector('.arrival-time, .arr')
                    price_el = await card.query_selector('.price, .fare-amount')
                    flight_el = await card.query_selector('.flight-number, .flight-id')

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "flight_number": await flight_el.inner_text() if flight_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[VuelingScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
