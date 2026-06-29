"""Pydantic v2 schemas for Accommodation — request/response DTOs."""
from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AccommodationBase(BaseModel):
    """Shared fields for accommodation schemas."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    country_code: str = Field(..., min_length=2, max_length=3, description="ISO 3166-1")
    check_in: date
    check_out: date
    room_type: str = Field(..., min_length=1, max_length=100)
    price_per_night_cents: int = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def checkout_after_checkin(self) -> "AccommodationBase":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class AccommodationCreate(AccommodationBase):
    """Schema for creating a new accommodation."""


class AccommodationUpdate(BaseModel):
    """Schema for partial accommodation updates (PATCH semantics)."""

    model_config = ConfigDict(populate_by_name=True)

    price_per_night_cents: int | None = Field(default=None, gt=0)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    metadata: dict[str, object] | None = None


class AccommodationRead(AccommodationBase):
    """Schema for reading an accommodation from the API."""

    id: UUID = Field(default_factory=uuid4)
    created_at: date
    updated_at: date

    model_config = ConfigDict(from_attributes=True)
