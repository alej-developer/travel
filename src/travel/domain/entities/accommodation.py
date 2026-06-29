"""Accommodation domain entity — pure dataclass, no ORM dependency."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4


@dataclass
class AccommodationEntity:
    """Represents an accommodation offer in the domain model."""

    name: str
    address: str
    city: str
    country_code: str
    check_in: date
    check_out: date
    room_type: str
    price_per_night_cents: int
    currency: str
    star_rating: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: date = field(default_factory=date.today)
    updated_at: date = field(default_factory=date.today)

    def total_nights(self) -> int:
        """Return number of nights for the stay."""
        return (self.check_out - self.check_in).days

    def total_price_cents(self) -> int:
        """Return total price for the entire stay."""
        return self.price_per_night_cents * self.total_nights()
