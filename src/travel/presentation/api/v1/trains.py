"""Trains router — v1 API endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from travel.application.schemas.train import TrainCreate, TrainRead, TrainUpdate
from travel.presentation.dependencies import DbSession

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("/", response_model=list[TrainRead], summary="List trains")
async def list_trains(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[TrainRead]:
    """Return a paginated list of available train journeys."""
    return []


@router.get("/{train_id}", response_model=TrainRead, summary="Get a train by ID")
async def get_train(train_id: UUID, db: DbSession) -> TrainRead:
    """Retrieve a single train journey by its UUID."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Train not found")


@router.post(
    "/",
    response_model=TrainRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a train",
)
async def create_train(payload: TrainCreate, db: DbSession) -> TrainRead:
    """Create a new train journey record."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )


@router.patch("/{train_id}", response_model=TrainRead, summary="Update a train")
async def update_train(train_id: UUID, payload: TrainUpdate, db: DbSession) -> TrainRead:
    """Partially update a train journey."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )


@router.delete(
    "/{train_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a train",
)
async def delete_train(train_id: UUID, db: DbSession) -> None:
    """Delete a train journey by UUID."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet"
    )
