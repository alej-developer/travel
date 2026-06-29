"""Abstract repository interface for Accommodation domain entity."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from travel.domain.entities.accommodation import AccommodationEntity


class AbstractAccommodationRepository(ABC):
    """Port (interface) that infrastructure must satisfy."""

    @abstractmethod
    async def get_by_id(self, accommodation_id: UUID) -> AccommodationEntity | None:
        """Retrieve an accommodation by its UUID."""
        ...

    @abstractmethod
    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[AccommodationEntity]:
        """Return a paginated list of accommodations."""
        ...

    @abstractmethod
    async def save(self, accommodation: AccommodationEntity) -> AccommodationEntity:
        """Persist an accommodation entity and return the saved version."""
        ...

    @abstractmethod
    async def delete(self, accommodation_id: UUID) -> bool:
        """Delete an accommodation by UUID. Returns True if deleted."""
        ...
