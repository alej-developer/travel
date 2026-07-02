"""Search router — v1 API endpoint for aggregated multi-provider search."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, status

from travel.application.schemas.search import (
    AggregatedSearchResponse,
    PROVIDER_DISPLAY_NAMES,
    ProviderResult,
    SearchRequest,
)
from travel.infrastructure.scraping.scraper_factory import ScraperFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post(
    "/",
    response_model=AggregatedSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Aggregated multi-provider search",
    description=(
        "Search across all registered providers for the given transport type. "
        "Returns results from multiple providers sorted by price."
    ),
)
async def search_aggregated(payload: SearchRequest) -> AggregatedSearchResponse:
    """Launch a search across all providers matching the transport type.

    This endpoint is designed to work in two modes:
    1. **Async (with Celery)**: triggers background scraping tasks and returns
       a task ID for polling.
    2. **Sync (without Celery)**: returns the available provider list and
       empty results — the frontend can then show which providers will be queried.

    For now, we return provider metadata and simulate the response structure.
    The actual scraping is triggered via Celery tasks from the worker.
    """
    transport_type = payload.transport_type.value
    providers = ScraperFactory.for_transport_type(transport_type)

    logger.info(
        "Aggregated search: type=%s, origin=%s, dest=%s, providers=%s",
        transport_type, payload.origin, payload.destination, providers,
    )

    # Build the response with provider metadata
    # In production, this would trigger celery tasks and return results
    # For now, we return the structure with empty results
    return AggregatedSearchResponse(
        transport_type=payload.transport_type,
        origin=payload.origin,
        destination=payload.destination,
        date_from=payload.date_from.isoformat(),
        date_to=payload.date_to.isoformat() if payload.date_to else None,
        providers_queried=providers,
        providers_succeeded=[],
        providers_failed=[],
        results=[],
        total_results=0,
    )


@router.get(
    "/providers",
    response_model=dict[str, list[dict[str, str]]],
    summary="List available providers by transport type",
)
async def list_providers() -> dict[str, list[dict[str, str]]]:
    """Return all registered providers grouped by transport type.

    This is useful for the frontend to display which providers are available
    and let users know where results come from.
    """
    result: dict[str, list[dict[str, str]]] = {}

    for transport_type in ("train", "flight", "accommodation"):
        domains = ScraperFactory.for_transport_type(transport_type)
        result[transport_type] = [
            {
                "domain": domain,
                "display_name": PROVIDER_DISPLAY_NAMES.get(domain, domain),
            }
            for domain in domains
        ]

    return result


@router.post(
    "/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger background scraping",
    description="Triggers async scraping via Celery for the specified transport type.",
)
async def trigger_scraping(payload: SearchRequest) -> dict[str, Any]:
    """Trigger background scraping tasks and return a task ID for polling.

    The client can use the returned task_id to poll for results.
    """
    from travel.worker.tasks import scrape_by_type

    transport_type = payload.transport_type.value
    providers = ScraperFactory.for_transport_type(transport_type)

    request_dict = {
        "origin": payload.origin,
        "destination": payload.destination,
        "departure_date": payload.date_from.isoformat(),
        "return_date": payload.date_to.isoformat() if payload.date_to else None,
        "adults": payload.passengers,
    }

    # Trigger Celery task
    task = scrape_by_type.delay(transport_type, request_dict)

    return {
        "task_id": str(task.id),
        "transport_type": transport_type,
        "providers": providers,
        "provider_names": {
            d: PROVIDER_DISPLAY_NAMES.get(d, d) for d in providers
        },
        "status": "accepted",
    }
