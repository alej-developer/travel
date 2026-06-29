"""Abstract repository interface for Train domain entity."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from travel.domain.entities.train import TrainEntity


class AbstractTrainRepository(ABC):
    """Port (interface) that infrastructure must satisfy."""

    @abstractmethod
    async def get_by_id(self, train_id: UUID) -> TrainEntity | None:
        """Retrieve a train journey by its UUID."""
        ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[TrainEntity]:
        """Return a paginated list of train journeys."""
        ...

    @abstractmethod
    async def save(self, train: TrainEntity) -> TrainEntity:
        """Persist a train entity and return the saved version."""
        ...

    @abstractmethod
    async def delete(self, train_id: UUID) -> bool:
        """Delete a train journey by UUID. Returns True if deleted."""
        ...
