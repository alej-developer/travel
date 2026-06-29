"""Flight domain entity — pure dataclass, no ORM dependency."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class FlightEntity:
    """Represents a flight offer in the domain model.

    All monetary amounts are stored in minor units (cents) to avoid
    floating-point rounding issues.
    """

    origin: str
    destination: str
    departure_at: datetime
    arrival_at: datetime
    airline: str
    flight_number: str
    price_cents: int
    currency: str
    metadata: dict[str, object] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def duration_minutes(self) -> int:
        """Return flight duration in minutes."""
        delta = self.arrival_at - self.departure_at
        return int(delta.total_seconds() // 60)
