"""SNCF Connect scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class SncfScraper(BaseScraper):
    """Scrapes train journeys from sncf-connect.com — French & international trains."""

    domain = "sncf-connect.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.sncf-connect.com/en/train-search"
            f"?origin={request.origin}"
            f"&destination={request.destination}"
            f"&outward={request.departure_date}"
            f"&passengers={request.adults}"
        )

        logger.info("[SncfScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('#onetrust-accept-btn-handler', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector('[class*="proposal"], .travel-proposal', timeout=30_000)

            cards = await page.query_selector_all('[class*="proposal"], .travel-proposal')
            for card in cards:
                try:
                    dep_el = await card.query_selector('[class*="departure"], .departure-time')
                    arr_el = await card.query_selector('[class*="arrival"], .arrival-time')
                    price_el = await card.query_selector('[class*="price"], .price')
                    duration_el = await card.query_selector('[class*="duration"], .duration')
                    train_el = await card.query_selector('[class*="train-type"], .train-number')

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "train_type": await train_el.inner_text() if train_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[SncfScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
