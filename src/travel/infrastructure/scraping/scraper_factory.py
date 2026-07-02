"""ScraperFactory — maps provider domains to scraper strategies.

Architecture
------------
The factory uses a registry dict (``_REGISTRY``) that maps a domain string to
its concrete :class:`~travel.infrastructure.scraping.base_scraper.BaseScraper`
class.  Registration is explicit (no auto-discovery magic) to keep the
dependency graph deterministic and mypy-friendly.

Usage
-----
    scraper = ScraperFactory.create("booking.com")
    result = await scraper.scrape(page, request)

    # Or resolve by URL
    scraper = ScraperFactory.from_url("https://www.airbnb.com/s/Madrid/homes")

    # Get scrapers for a specific transport type
    domains = ScraperFactory.for_transport_type("train")

Extending
---------
To add a new provider, create a module in ``providers/`` implementing
:class:`BaseScraper` and register it here::

    ScraperFactory.register("newprovider.com", NewProviderScraper)
"""
from __future__ import annotations

import logging
from typing import ClassVar

from travel.infrastructure.scraping.base_scraper import BaseScraper

# ── Existing providers ──────────────────────────────────────────────────────
from travel.infrastructure.scraping.providers.airbnb import AirbnbScraper
from travel.infrastructure.scraping.providers.booking import BookingScraper
from travel.infrastructure.scraping.providers.iberia import IberiaScraper
from travel.infrastructure.scraping.providers.renfe import RenfeScraper

# ── New train providers ─────────────────────────────────────────────────────
from travel.infrastructure.scraping.providers.trenes_com import TrenesComScraper
from travel.infrastructure.scraping.providers.sncf import SncfScraper
from travel.infrastructure.scraping.providers.trainline import TrainlineScraper
from travel.infrastructure.scraping.providers.ouigo import OuigoScraper
from travel.infrastructure.scraping.providers.iryo import IryoScraper

# ── New flight providers ────────────────────────────────────────────────────
from travel.infrastructure.scraping.providers.ryanair import RyanairScraper
from travel.infrastructure.scraping.providers.vueling import VuelingScraper
from travel.infrastructure.scraping.providers.easyjet import EasyJetScraper
from travel.infrastructure.scraping.providers.skyscanner import SkyscannerScraper
from travel.infrastructure.scraping.providers.google_flights import GoogleFlightsScraper

# ── New accommodation providers ─────────────────────────────────────────────
from travel.infrastructure.scraping.providers.vrbo import VrboScraper
from travel.infrastructure.scraping.providers.ruralia import RuraliaScraper
from travel.infrastructure.scraping.providers.escapada_rural import EscapadaRuralScraper
from travel.infrastructure.scraping.providers.idealista import IdealistaScraper
from travel.infrastructure.scraping.providers.trivago import TrivagoScraper

logger = logging.getLogger(__name__)


class UnknownProviderError(Exception):
    """Raised when no scraper is registered for the requested domain."""


# ── Transport-type to domain mapping ────────────────────────────────────────

_TRANSPORT_DOMAINS: dict[str, list[str]] = {
    "train": [
        "renfe.com",
        "trenes.com",
        "sncf-connect.com",
        "thetrainline.com",
        "ouigo.com",
        "iryo.eu",
    ],
    "flight": [
        "iberia.com",
        "ryanair.com",
        "vueling.com",
        "easyjet.com",
        "skyscanner.es",
        "google.com/travel/flights",
    ],
    "accommodation": [
        "booking.com",
        "airbnb.com",
        "vrbo.com",
        "ruralia.com",
        "escapadarural.com",
        "idealista.com",
        "trivago.es",
    ],
}


class ScraperFactory:
    """Registry-based factory that instantiates the correct scraper strategy.

    All registered scrapers are singletons within the factory — the same
    instance is returned on repeated ``create()`` calls for the same domain,
    since scrapers are stateless by design.
    """

    _REGISTRY: ClassVar[dict[str, type[BaseScraper]]] = {
        # ── Trains ──────────────────────────────────────────────────────────
        "renfe.com":                  RenfeScraper,
        "trenes.com":                 TrenesComScraper,
        "sncf-connect.com":          SncfScraper,
        "thetrainline.com":          TrainlineScraper,
        "ouigo.com":                  OuigoScraper,
        "iryo.eu":                    IryoScraper,
        # ── Flights ─────────────────────────────────────────────────────────
        "iberia.com":                 IberiaScraper,
        "ryanair.com":                RyanairScraper,
        "vueling.com":                VuelingScraper,
        "easyjet.com":                EasyJetScraper,
        "skyscanner.es":              SkyscannerScraper,
        "google.com/travel/flights":  GoogleFlightsScraper,
        # ── Accommodations ──────────────────────────────────────────────────
        "booking.com":                BookingScraper,
        "airbnb.com":                 AirbnbScraper,
        "vrbo.com":                   VrboScraper,
        "ruralia.com":                RuraliaScraper,
        "escapadarural.com":          EscapadaRuralScraper,
        "idealista.com":              IdealistaScraper,
        "trivago.es":                 TrivagoScraper,
    }

    _INSTANCES: ClassVar[dict[str, BaseScraper]] = {}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @classmethod
    def create(cls, domain: str) -> BaseScraper:
        """Return a scraper instance for *domain*.

        Parameters
        ----------
        domain:
            Provider domain key, e.g. ``"booking.com"``.

        Raises
        ------
        UnknownProviderError
            If *domain* has no registered scraper.
        """
        domain = domain.lower().strip()
        if domain not in cls._INSTANCES:
            scraper_cls = cls._REGISTRY.get(domain)
            if scraper_cls is None:
                available = ", ".join(sorted(cls._REGISTRY))
                raise UnknownProviderError(
                    f"No scraper registered for domain '{domain}'. "
                    f"Available: {available}"
                )
            cls._INSTANCES[domain] = scraper_cls()
            logger.debug("ScraperFactory: created %s for domain=%r", scraper_cls.__name__, domain)

        return cls._INSTANCES[domain]

    @classmethod
    def from_url(cls, url: str) -> BaseScraper:
        """Resolve a scraper from a full URL.

        Extracts the registerable domain by matching against all known domains.
        This supports URLs like ``https://www.booking.com/searchresults.html``.

        Raises
        ------
        UnknownProviderError
            If no registered domain matches the URL.
        """
        url_lower = url.lower()
        for domain in cls._REGISTRY:
            if domain in url_lower:
                return cls.create(domain)
        raise UnknownProviderError(
            f"Cannot resolve a scraper from URL: '{url}'. "
            f"Registered domains: {', '.join(sorted(cls._REGISTRY))}"
        )

    @classmethod
    def register(cls, domain: str, scraper_cls: type[BaseScraper]) -> None:
        """Dynamically register a new provider scraper at runtime.

        This is useful for plugin-style extension without modifying this file.
        """
        domain = domain.lower().strip()
        cls._REGISTRY[domain] = scraper_cls
        # Invalidate cached instance if any
        cls._INSTANCES.pop(domain, None)
        logger.info("ScraperFactory: registered %s for domain=%r", scraper_cls.__name__, domain)

    @classmethod
    def available_domains(cls) -> list[str]:
        """Return sorted list of all registered provider domains."""
        return sorted(cls._REGISTRY.keys())

    @classmethod
    def for_transport_type(cls, transport_type: str) -> list[str]:
        """Return the list of domains relevant to a transport type.

        Parameters
        ----------
        transport_type:
            One of ``"train"``, ``"flight"``, or ``"accommodation"``.

        Returns
        -------
        list[str]
            Sorted list of provider domains for this transport type.
            Returns all domains if *transport_type* is not recognised.
        """
        transport_type = transport_type.lower().strip()
        domains = _TRANSPORT_DOMAINS.get(transport_type)
        if domains is None:
            logger.warning(
                "Unknown transport type %r — returning all domains", transport_type
            )
            return cls.available_domains()
        # Only return domains that are actually registered
        return sorted(d for d in domains if d in cls._REGISTRY)
