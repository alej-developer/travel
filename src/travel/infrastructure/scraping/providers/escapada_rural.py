"""Escapada Rural scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class EscapadaRuralScraper(BaseScraper):
    """Scrapes rural accommodations from escapadarural.com — Spanish rural tourism."""

    domain = "escapadarural.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.escapadarural.com/casas-rurales/{request.destination.lower()}"
            f"?fecha_entrada={request.departure_date}"
            f"&fecha_salida={request.return_date or ''}"
            f"&num_personas={request.adults}"
        )

        logger.info("[EscapadaRuralScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('#didomi-notice-agree-button, .accept-cookies', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector(
                '.property-card, .accommodation-card, .listing', timeout=25_000
            )

            cards = await page.query_selector_all(
                '.property-card, .accommodation-card, .listing'
            )
            for card in cards:
                try:
                    name_el = await card.query_selector('.name, h2, .title')
                    price_el = await card.query_selector('.price, .precio')
                    location_el = await card.query_selector('.location, .zona')
                    capacity_el = await card.query_selector('.capacity, .plazas')
                    type_el = await card.query_selector('.type, .tipo-alojamiento')
                    rating_el = await card.query_selector('.rating, .valoracion')

                    raw_items.append({
                        "name": await name_el.inner_text() if name_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "location": await location_el.inner_text() if location_el else None,
                        "capacity": await capacity_el.inner_text() if capacity_el else None,
                        "accommodation_type": await type_el.inner_text() if type_el else None,
                        "rating_raw": await rating_el.inner_text() if rating_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[EscapadaRuralScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
