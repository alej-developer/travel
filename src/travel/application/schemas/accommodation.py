"""Pydantic v2 schemas for Accommodation — request/response DTOs with strict input sanitisation."""
from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from travel.application.schemas.validators import (
    CurrencyCode,
    IataCode,
    SafeAddress,
    SafeMetadata,
    SafeName,
    SafeRoomType,
    SafeStationName,
)


class AccommodationBase(BaseModel):
    """Shared fields for accommodation schemas.

    All text inputs are validated against a whitelist regex — blocks SQL
    operators (``'``, ``--``, ``;``), MongoDB injection operators (``$``, ``{``),
    and oversized payloads.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: SafeName
    address: SafeAddress
    city: SafeStationName
    country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 country code (uppercase, e.g. ES)",
    )
    check_in: date
    check_out: date
    room_type: SafeRoomType
    price_per_night_cents: int = Field(..., gt=0, lt=100_000_000)
    currency: CurrencyCode
    star_rating: int | None = Field(default=None, ge=1, le=5)
    metadata: SafeMetadata = Field(default_factory=dict)

    @model_validator(mode="after")
    def checkout_after_checkin(self) -> "AccommodationBase":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self

    @model_validator(mode="after")
    def max_stay_duration(self) -> "AccommodationBase":
        nights = (self.check_out - self.check_in).days
        if nights > 365:
            raise ValueError("Stay duration cannot exceed 365 nights")
        return self


class AccommodationCreate(AccommodationBase):
    """Schema for creating a new accommodation."""


class AccommodationUpdate(BaseModel):
    """Schema for partial accommodation updates (PATCH semantics)."""

    model_config = ConfigDict(populate_by_name=True)

    price_per_night_cents: int | None = Field(default=None, gt=0, lt=100_000_000)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    metadata: SafeMetadata | None = None


class AccommodationRead(AccommodationBase):
    """Schema for reading an accommodation from the API."""

    id: UUID = Field(default_factory=uuid4)
    created_at: date
    updated_at: date

    model_config = ConfigDict(from_attributes=True)
