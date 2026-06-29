"""Abstract repository interface for Flight domain entity."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from travel.domain.entities.flight import FlightEntity


class AbstractFlightRepository(ABC):
    """Port (interface) that infrastructure must satisfy."""

    @abstractmethod
    async def get_by_id(self, flight_id: UUID) -> FlightEntity | None:
        """Retrieve a flight by its UUID."""
        ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[FlightEntity]:
        """Return a paginated list of flights."""
        ...

    @abstractmethod
    async def save(self, flight: FlightEntity) -> FlightEntity:
        """Persist a flight entity and return the saved version."""
        ...

    @abstractmethod
    async def delete(self, flight_id: UUID) -> bool:
        """Delete a flight by UUID. Returns True if deleted, False if not found."""
        ...
