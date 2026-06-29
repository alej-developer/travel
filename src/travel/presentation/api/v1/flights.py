"""Flights router — v1 API endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from travel.application.schemas.flight import FlightCreate, FlightRead, FlightUpdate
from travel.presentation.dependencies import DbSession

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("/", response_model=list[FlightRead], summary="List flights")
async def list_flights(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[FlightRead]:
    """Return a paginated list of available flights."""
    # TODO: delegate to use-case / repository
    return []


@router.get("/{flight_id}", response_model=FlightRead, summary="Get a flight by ID")
async def get_flight(flight_id: UUID, db: DbSession) -> FlightRead:
    """Retrieve a single flight by its UUID."""
    # TODO: delegate to use-case / repository
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")


@router.post(
    "/",
    response_model=FlightRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a flight",
)
async def create_flight(payload: FlightCreate, db: DbSession) -> FlightRead:
    """Create a new flight record."""
    # TODO: delegate to use-case / repository
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )


@router.patch("/{flight_id}", response_model=FlightRead, summary="Update a flight")
async def update_flight(
    flight_id: UUID, payload: FlightUpdate, db: DbSession
) -> FlightRead:
    """Partially update a flight."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )


@router.delete(
    "/{flight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a flight",
)
async def delete_flight(flight_id: UUID, db: DbSession) -> None:
    """Delete a flight by UUID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )
