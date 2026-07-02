"""Iryo scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class IryoScraper(BaseScraper):
    """Scrapes high-speed trains from iryo.eu — private Spanish operator."""

    domain = "iryo.eu"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://iryo.eu/es/search"
            f"?origin={request.origin}"
            f"&destination={request.destination}"
            f"&outbound={request.departure_date}"
            f"&adults={request.adults}"
        )

        logger.info("[IryoScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookies
            try:
                await page.click('#accept-cookies, .cookie-accept-btn', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector('.journey-option, .train-result', timeout=25_000)

            cards = await page.query_selector_all('.journey-option, .train-result')
            for card in cards:
                try:
                    dep_el = await card.query_selector('.departure-time, .time-start')
                    arr_el = await card.query_selector('.arrival-time, .time-end')
                    price_el = await card.query_selector('.price, .journey-price')
                    class_el = await card.query_selector('.class-name, .service-class')
                    duration_el = await card.query_selector('.duration, .travel-time')

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "service_class": await class_el.inner_text() if class_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[IryoScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
