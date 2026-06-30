"""Pydantic v2 schemas for Train — request/response DTOs with strict input sanitisation."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from travel.application.schemas.validators import (
    CurrencyCode,
    SafeMetadata,
    SafeOperatorName,
    SafeRoomType,
    SafeStationName,
)


class TrainBase(BaseModel):
    """Shared fields for train schemas.

    All text fields use whitelisted character sets — blocks SQL/NoSQL injection.
    """

    model_config = ConfigDict(populate_by_name=True)

    origin_station: SafeStationName
    destination_station: SafeStationName
    departure_at: datetime
    arrival_at: datetime
    operator: SafeOperatorName
    train_number: str = Field(
        ...,
        min_length=1,
        max_length=20,
        pattern=r"^[\w\-]+$",
        description="Train number: alphanumeric and hyphens only",
    )
    service_class: SafeRoomType = Field(..., description="e.g. FIRST, SECOND, BUSINESS")
    price_cents: int = Field(..., gt=0, lt=100_000_000)
    currency: CurrencyCode
    metadata: SafeMetadata = Field(default_factory=dict)

    @model_validator(mode="after")
    def arrival_after_departure(self) -> "TrainBase":
        if self.arrival_at <= self.departure_at:
            raise ValueError("arrival_at must be after departure_at")
        return self

    @model_validator(mode="after")
    def origin_not_equal_destination(self) -> "TrainBase":
        if self.origin_station.upper() == self.destination_station.upper():
            raise ValueError("origin_station and destination_station must be different")
        return self


class TrainCreate(TrainBase):
    """Schema for creating a new train journey."""


class TrainUpdate(BaseModel):
    """Schema for partial train updates (PATCH semantics)."""

    model_config = ConfigDict(populate_by_name=True)

    price_cents: int | None = Field(default=None, gt=0, lt=100_000_000)
    service_class: SafeRoomType | None = None
    metadata: SafeMetadata | None = None


class TrainRead(TrainBase):
    """Schema for reading a train journey from the API."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
