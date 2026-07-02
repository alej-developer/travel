"""Trainline scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class TrainlineScraper(BaseScraper):
    """Scrapes train & bus journeys from thetrainline.com — European aggregator."""

    domain = "thetrainline.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.thetrainline.com/book/results"
            f"?origin={request.origin}"
            f"&destination={request.destination}"
            f"&outwardDate={request.departure_date}T08:00:00"
            f"&outwardDateType=departAfter"
            f"&journeySearchType=single"
            f"&passengers[]={request.adults}-0"
        )

        logger.info("[TrainlineScraper] GET %s", url)
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
                '[data-testid="journey-card"], .result-card', timeout=25_000
            )

            cards = await page.query_selector_all(
                '[data-testid="journey-card"], .result-card'
            )
            for card in cards:
                try:
                    dep_el = await card.query_selector(
                        '[data-testid="departure-time"], .departure'
                    )
                    arr_el = await card.query_selector(
                        '[data-testid="arrival-time"], .arrival'
                    )
                    price_el = await card.query_selector(
                        '[data-testid="price"], .price'
                    )
                    duration_el = await card.query_selector(
                        '[data-testid="duration"], .duration'
                    )
                    operator_el = await card.query_selector(
                        '[data-testid="operator"], .operator'
                    )

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "operator": await operator_el.inner_text() if operator_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[TrainlineScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
