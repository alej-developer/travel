"""SQLAlchemy 2.0 ORM model for the ``flights`` table."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from travel.infrastructure.database.base import Base


class FlightModel(Base):
    """Persistent representation of a flight offer.

    The ``metadata_`` column (mapped as ``metadata``) uses PostgreSQL's native
    JSONB type to store variable, provider-specific attributes without schema
    migrations.
    """

    __tablename__ = "flights"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    origin: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    departure_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    airline: Mapped[str] = mapped_column(String(10), nullable=False)
    flight_number: Mapped[str] = mapped_column(String(10), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    # JSONB for variable provider-specific attributes
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="'{}'::jsonb",
    )

    def __repr__(self) -> str:
        return (
            f"<FlightModel id={self.id} "
            f"{self.origin}→{self.destination} {self.departure_at}>"
        )
