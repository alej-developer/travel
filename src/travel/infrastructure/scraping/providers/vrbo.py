"""Vrbo scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class VrboScraper(BaseScraper):
    """Scrapes vacation rentals from vrbo.com — holiday homes & rural properties."""

    domain = "vrbo.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.vrbo.com/search"
            f"?destination={request.destination}"
            f"&startDate={request.departure_date}"
            f"&endDate={request.return_date or ''}"
            f"&adults={request.adults}"
        )

        logger.info("[VrboScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('#onetrust-accept-btn-handler', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector(
                '[data-stid="property-listing"], .property-card', timeout=25_000
            )

            cards = await page.query_selector_all(
                '[data-stid="property-listing"], .property-card'
            )
            for card in cards:
                try:
                    name_el = await card.query_selector(
                        '[data-stid="content-hotel-title"], .property-name, h3'
                    )
                    price_el = await card.query_selector(
                        '[data-stid="content-hotel-price"], .price-total, .price'
                    )
                    rating_el = await card.query_selector(
                        '[data-stid="content-hotel-reviews"], .review-score'
                    )
                    type_el = await card.query_selector('.property-type, .listing-type')

                    raw_items.append({
                        "name": await name_el.inner_text() if name_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "rating_raw": await rating_el.inner_text() if rating_el else None,
                        "property_type": await type_el.inner_text() if type_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[VrboScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
