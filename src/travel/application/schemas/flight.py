"""Pydantic v2 schemas for Flight — request/response DTOs with strict input sanitisation."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from travel.application.schemas.validators import (
    CurrencyCode,
    IataCode,
    SafeAirlineName,
    SafeFlightNumber,
    SafeMetadata,
)


class FlightBase(BaseModel):
    """Shared fields for flight schemas.

    All string inputs are validated with:
    - Strict regex whitelisting (no SQL/NoSQL injection characters)
    - Hard length limits (prevent buffer exhaustion)
    - Domain-specific format validation (IATA codes, flight numbers, ISO currency)
    """

    model_config = ConfigDict(populate_by_name=True)

    origin: IataCode
    destination: IataCode
    departure_at: datetime
    arrival_at: datetime
    airline: SafeAirlineName
    flight_number: SafeFlightNumber
    price_cents: int = Field(..., gt=0, lt=100_000_000, description="Price in minor units (cents)")
    currency: CurrencyCode
    metadata: SafeMetadata = Field(default_factory=dict)

    @model_validator(mode="after")
    def arrival_after_departure(self) -> "FlightBase":
        if self.arrival_at <= self.departure_at:
            raise ValueError("arrival_at must be after departure_at")
        return self

    @model_validator(mode="after")
    def origin_not_equal_destination(self) -> "FlightBase":
        if self.origin == self.destination:
            raise ValueError("origin and destination must be different airports")
        return self


class FlightCreate(FlightBase):
    """Schema for creating a new flight."""


class FlightUpdate(BaseModel):
    """Schema for partial flight updates (PATCH semantics)."""

    model_config = ConfigDict(populate_by_name=True)

    price_cents: int | None = Field(default=None, gt=0, lt=100_000_000)
    metadata: SafeMetadata | None = None


class FlightRead(FlightBase):
    """Schema for reading a flight from the API."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
