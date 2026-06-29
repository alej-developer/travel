"""Pydantic v2 schemas for Flight — request/response DTOs."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FlightBase(BaseModel):
    """Shared fields for flight schemas."""

    model_config = ConfigDict(populate_by_name=True)

    origin: str = Field(..., min_length=3, max_length=3, description="IATA origin code")
    destination: str = Field(
        ..., min_length=3, max_length=3, description="IATA destination code"
    )
    departure_at: datetime
    arrival_at: datetime
    airline: str = Field(..., min_length=2, max_length=10)
    flight_number: str = Field(..., min_length=2, max_length=10)
    price_cents: int = Field(..., gt=0, description="Price in minor currency units")
    currency: str = Field(..., min_length=3, max_length=3)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def arrival_after_departure(self) -> "FlightBase":
        if self.arrival_at <= self.departure_at:
            raise ValueError("arrival_at must be after departure_at")
        return self


class FlightCreate(FlightBase):
    """Schema for creating a new flight."""


class FlightUpdate(BaseModel):
    """Schema for partial flight updates (PATCH semantics)."""

    model_config = ConfigDict(populate_by_name=True)

    price_cents: int | None = Field(default=None, gt=0)
    metadata: dict[str, object] | None = None


class FlightRead(FlightBase):
    """Schema for reading a flight from the API."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
