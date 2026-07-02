"""Ryanair scraper strategy."""
from __future__ import annotations

import logging

from playwright.async_api import Page

from travel.infrastructure.scraping.base_scraper import BaseScraper, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)


class RyanairScraper(BaseScraper):
    """Scrapes flights from ryanair.com — Europe's largest low-cost carrier."""

    domain = "ryanair.com"

    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        url = (
            f"https://www.ryanair.com/api/booking/v4/es-es/availability"
            f"?ADT={request.adults}"
            f"&CHD=0&INF=0&TEEN=0"
            f"&DateOut={request.departure_date}"
            f"&Origin={request.origin}"
            f"&Destination={request.destination}"
            f"&IncludeConnectingFlights=false"
            f"&RoundTrip={'true' if request.return_date else 'false'}"
            f"&ToUs=AGREED"
        )

        logger.info("[RyanairScraper] GET %s", url)
        raw_items: list[dict[str, object]] = []
        errors: list[str] = []

        try:
            await page.goto(
                f"https://www.ryanair.com/es/es/trip/flights/select"
                f"?adults={request.adults}&teens=0&children=0&infants=0"
                f"&dateOut={request.departure_date}"
                f"&originIata={request.origin}&destinationIata={request.destination}"
                f"&isReturn={'true' if request.return_date else 'false'}",
                wait_until="domcontentloaded",
                timeout=30_000,
            )

            # Accept cookies
            try:
                await page.click('[data-ref="cookie.accept-all"]', timeout=5_000)
            except Exception:
                pass

            await page.wait_for_selector(
                '[data-e2e="flight-card"], .flight-card', timeout=30_000
            )

            cards = await page.query_selector_all(
                '[data-e2e="flight-card"], .flight-card'
            )
            for card in cards:
                try:
                    dep_el = await card.query_selector(
                        '[data-e2e="flight-card--departure-time"], .dep-time'
                    )
                    arr_el = await card.query_selector(
                        '[data-e2e="flight-card--arrival-time"], .arr-time'
                    )
                    price_el = await card.query_selector(
                        '[data-e2e="flight-card--price"], .price'
                    )
                    duration_el = await card.query_selector(
                        '[data-e2e="flight-card--duration"], .duration'
                    )

                    raw_items.append({
                        "departure_time": await dep_el.inner_text() if dep_el else None,
                        "arrival_time": await arr_el.inner_text() if arr_el else None,
                        "price_raw": await price_el.inner_text() if price_el else None,
                        "duration": await duration_el.inner_text() if duration_el else None,
                        "provider": self.domain,
                    })
                except Exception as exc:
                    errors.append(f"Card parse error: {exc}")

        except Exception as exc:
            logger.exception("[RyanairScraper] Fatal error")
            errors.append(str(exc))

        return ScrapeResult(
            provider=self.domain,
            raw_items=raw_items,
            errors=errors,
        )
