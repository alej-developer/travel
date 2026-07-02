"""Ruralia scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class RuraliaScraper(BaseScraper):
    """Scrapes rural houses from ruralia.com — Spanish rural tourism platform."""

    domain = "ruralia.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.ruralia.com/busqueda"
            f"?destino={request.destination}"
            f"&fecha_entrada={request.departure_date}"
            f"&fecha_salida={request.return_date or ''}"
            f"&personas={request.adults}"
        )

        logger.info("[RuraliaScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('.accept-cookies, #cookie-accept', timeout=4_000)
            except Exception:
                pass

            await page.wait_for_selector(
                '.property-card, .alojamiento-card, .listing-item', timeout=25_000
            )

            cards = await page.query_selector_all(
                '.property-card, .alojamiento-card, .listing-item'
            )
            for card in cards:
                try:
                    name_el = await card.query_selector('.property-name, h3, .title')
                    price_el = await card.query_selector('.price, .precio')
                    location_el = await card.query_selector('.location, .ubicacion')
                    capacity_el = await card.query_selector('.capacity, .capacidad')
                    rating_el = await card.query_selector('.rating, .puntuacion')

                    raw_items.append({
                        "name": await name_el.inner_text() if name_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "location": await location_el.inner_text() if location_el else None,
                        "capacity": await capacity_el.inner_text() if capacity_el else None,
                        "rating_raw": await rating_el.inner_text() if rating_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[RuraliaScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
