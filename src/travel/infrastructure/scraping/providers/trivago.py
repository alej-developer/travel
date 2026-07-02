"""Trivago scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class TrivagoScraper(BaseScraper):
    """Scrapes hotel offers from trivago.es — hotel metasearch engine."""

    domain = "trivago.es"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.trivago.es/es/srl"
            f"?search={request.destination}"
            f"&aDateRange[arr]={request.departure_date}"
            f"&aDateRange[dep]={request.return_date or ''}"
            f"&iRoomType=7"
            f"&iPathId=36"
        )

        logger.info("[TrivagoScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click(
                    '[data-testid="privacy-Be-Okay-With-It"], #onetrust-accept-btn-handler',
                    timeout=5_000,
                )
            except Exception:
                pass

            await page.wait_for_selector(
                '[data-testid="accommodation-list-element"], .hotel-card',
                timeout=25_000,
            )

            cards = await page.query_selector_all(
                '[data-testid="accommodation-list-element"], .hotel-card'
            )
            for card in cards:
                try:
                    name_el = await card.query_selector(
                        '[data-testid="item-name"], .hotel-name, h3'
                    )
                    price_el = await card.query_selector(
                        '[data-testid="recommended-price"], .price'
                    )
                    rating_el = await card.query_selector(
                        '[data-testid="rating-score"], .rating-score'
                    )
                    source_el = await card.query_selector(
                        '[data-testid="deal-label"], .deal-source'
                    )

                    raw_items.append({
                        "name": await name_el.inner_text() if name_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "rating_raw": await rating_el.inner_text() if rating_el else None,
                        "deal_source": await source_el.inner_text() if source_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[TrivagoScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
