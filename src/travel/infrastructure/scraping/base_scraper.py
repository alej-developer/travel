"""Base scraper interface — all concrete scrapers must implement this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Page


@dataclass
class ScrapeRequest:
    """Standardised input for all scrapers."""

    origin: str
    destination: str
    departure_date: str           # ISO-8601 date string "YYYY-MM-DD"
    return_date: str | None = None
    adults: int = 1
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapeResult:
    """Standardised output from all scrapers."""

    provider: str
    raw_items: list[dict[str, Any]]
    errors: list[str] = field(default_factory=list)
    was_rate_limited: bool = False


class BaseScraper(ABC):
    """Abstract base class for all provider scrapers.

    Concrete scrapers receive a Playwright :class:`~playwright.async_api.Page`
    that has already been configured with anti-detection measures, proxy,
    and network middleware by the orchestrator.
    """

    #: Override in subclasses — used for logging and circuit-breaker keys
    domain: str = ""

    @abstractmethod
    async def scrape(self, page: Page, request: ScrapeRequest) -> ScrapeResult:
        """Execute the scraping logic and return a standardised result.

        Parameters
        ----------
        page:
            A pre-configured Playwright page (stealth + middleware applied).
        request:
            Standardised search parameters.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} domain={self.domain!r}>"
