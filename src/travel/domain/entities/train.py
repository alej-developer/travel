"""Train domain entity — pure dataclass, no ORM dependency."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class TrainEntity:
    """Represents a train journey offer in the domain model."""

    origin_station: str
    destination_station: str
    departure_at: datetime
    arrival_at: datetime
    operator: str
    train_number: str
    service_class: str
    price_cents: int
    currency: str
    metadata: dict[str, object] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def duration_minutes(self) -> int:
        """Return journey duration in minutes."""
        delta = self.arrival_at - self.departure_at
        return int(delta.total_seconds() // 60)
