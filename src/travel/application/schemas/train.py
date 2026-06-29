"""Pydantic v2 schemas for Train — request/response DTOs."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TrainBase(BaseModel):
    """Shared fields for train schemas."""

    model_config = ConfigDict(populate_by_name=True)

    origin_station: str = Field(..., min_length=2, max_length=100)
    destination_station: str = Field(..., min_length=2, max_length=100)
    departure_at: datetime
    arrival_at: datetime
    operator: str = Field(..., min_length=2, max_length=100)
    train_number: str = Field(..., min_length=1, max_length=20)
    service_class: str = Field(..., description="e.g. FIRST, SECOND, BUSINESS")
    price_cents: int = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def arrival_after_departure(self) -> "TrainBase":
        if self.arrival_at <= self.departure_at:
            raise ValueError("arrival_at must be after departure_at")
        return self


class TrainCreate(TrainBase):
    """Schema for creating a new train journey."""


class TrainUpdate(BaseModel):
    """Schema for partial train updates (PATCH semantics)."""

    model_config = ConfigDict(populate_by_name=True)

    price_cents: int | None = Field(default=None, gt=0)
    service_class: str | None = None
    metadata: dict[str, object] | None = None


class TrainRead(TrainBase):
    """Schema for reading a train journey from the API."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
