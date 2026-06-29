"""Booking.com scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class BookingScraper(BaseScraper):
    """Scrapes accommodation offers from booking.com.

    Strategy
    --------
    1. Navigate to the search URL with query-string parameters.
    2. Wait for the property card list to appear.
    3. Extract price, name, rating, and URL from each card via CSS selectors.
    4. Return raw dicts — normalisation happens in the application layer.
    """

    domain = "booking.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.booking.com/searchresults.html"
            f"?ss={request.destination}"
            f"&checkin={request.departure_date}"
            f"&checkout={request.return_date or ''}"
            f"&group_adults={request.adults}"
            f"&no_rooms=1"
            f"&lang=en-gb"
        )

        logger.info("[BookingScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookie banner if present
            try:
                await page.click('[id="onetrust-accept-btn-handler"]', timeout=4_000)
            except Exception:
                pass

            # Wait for property cards
            await page.wait_for_selector('[data-testid="property-card"]', timeout=20_000)

            cards = await page.query_selector_all('[data-testid="property-card"]')
            for card in cards:
                try:
                    name_el = await card.query_selector('[data-testid="title"]')
                    price_el = await card.query_selector('[data-testid="price-and-discounted-price"]')
                    score_el = await card.query_selector('[data-testid="review-score"]')

                    raw_items.append({
                        "name": await name_el.inner_text() if name_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "score_raw": await score_el.inner_text() if score_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[BookingScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
