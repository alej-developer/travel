"""Idealista scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class IdealistaScraper(BaseScraper):
    """Scrapes vacation rentals from idealista.com — Spanish real estate & holiday rentals."""

    domain = "idealista.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.idealista.com/alquiler-vacacional/{request.destination.lower()}/"
            f"?fechaEntrada={request.departure_date}"
            f"&fechaSalida={request.return_date or ''}"
        )

        logger.info("[IdealistaScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('#didomi-notice-agree-button, .accept-cookies', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector('.item-multimedia-container, .item', timeout=25_000)

            cards = await page.query_selector_all('article.item, .item-info-container')
            for card in cards:
                try:
                    name_el = await card.query_selector('.item-link, a.item-link')
                    price_el = await card.query_selector('.item-price, .price-row')
                    detail_el = await card.query_selector('.item-detail, .item-description')
                    location_el = await card.query_selector('.item-detail-char, .item-location')

                    raw_items.append({
                        "name": await name_el.inner_text() if name_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "details": await detail_el.inner_text() if detail_el else None,
                        "location": await location_el.inner_text() if location_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[IdealistaScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
