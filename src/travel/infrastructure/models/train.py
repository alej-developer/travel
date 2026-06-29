"""SQLAlchemy 2.0 ORM model for the ``trains`` table."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from travel.infrastructure.database.base import Base


class TrainModel(Base):
    """Persistent representation of a train journey offer."""

    __tablename__ = "trains"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    origin_station: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    destination_station: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    departure_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    operator: Mapped[str] = mapped_column(String(100), nullable=False)
    train_number: Mapped[str] = mapped_column(String(20), nullable=False)
    service_class: Mapped[str] = mapped_column(String(50), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="'{}'::jsonb",
    )

    def __repr__(self) -> str:
        return (
            f"<TrainModel id={self.id} "
            f"{self.origin_station}→{self.destination_station} {self.departure_at}>"
        )
