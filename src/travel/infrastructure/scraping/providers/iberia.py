"""Iberia scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class IberiaScraper(BaseScraper):
    """Scrapes flight offers from iberia.com."""

    domain = "iberia.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.iberia.com/vuelos-baratos/{request.origin.lower()}"
            f"-{request.destination.lower()}/"
            f"?fecha={request.departure_date.replace('-', '')}"
            f"&adult={request.adults}"
            f"&cabina=N"
        )

        logger.info("[IberiaScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Accept cookie consent
            try:
                await page.click('#onetrust-accept-btn-handler', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector('.flight-card', timeout=30_000)

            cards = await page.query_selector_all('.flight-card')
            for card in cards:
                try:
                    dep_el = await card.query_selector('.departure')
                    arr_el = await card.query_selector('.arrival')
                    price_el = await card.query_selector('.price')
                    raw_items.append({
                        "departure": await dep_el.inner_text() if dep_el else None,
                        "arrival": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[IberiaScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
