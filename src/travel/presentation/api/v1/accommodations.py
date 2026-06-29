"""Accommodations router — v1 API endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from travel.application.schemas.accommodation import (
    AccommodationCreate,
    AccommodationRead,
    AccommodationUpdate,
)
from travel.presentation.dependencies import DbSession

router = APIRouter(prefix="/accommodations", tags=["accommodations"])


@router.get("/", response_model=list[AccommodationRead], summary="List accommodations")
async def list_accommodations(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AccommodationRead]:
    """Return a paginated list of available accommodations."""
    return []


@router.get(
    "/{accommodation_id}",
    response_model=AccommodationRead,
    summary="Get an accommodation by ID",
)
async def get_accommodation(accommodation_id: UUID, db: DbSession) -> AccommodationRead:
    """Retrieve a single accommodation by its UUID."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found"
    )


@router.post(
    "/",
    response_model=AccommodationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an accommodation",
)
async def create_accommodation(
    payload: AccommodationCreate, db: DbSession
) -> AccommodationRead:
    """Create a new accommodation record."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )


@router.patch(
    "/{accommodation_id}",
    response_model=AccommodationRead,
    summary="Update an accommodation",
)
async def update_accommodation(
    accommodation_id: UUID, payload: AccommodationUpdate, db: DbSession
) -> AccommodationRead:
    """Partially update an accommodation."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )


@router.delete(
    "/{accommodation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an accommodation",
)
async def delete_accommodation(accommodation_id: UUID, db: DbSession) -> None:
    """Delete an accommodation by UUID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )
