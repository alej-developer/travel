"""SQLAlchemy 2.0 ORM model for the ``accommodations`` table."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from travel.infrastructure.database.base import Base


class AccommodationModel(Base):
    """Persistent representation of an accommodation offer."""

    __tablename__ = "accommodations"

    # Override Base id to use PG_UUID
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    # Override base timestamps to use Date for accommodations
    created_at: Mapped[datetime] = mapped_column(  # type: ignore[assignment]
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(  # type: ignore[assignment]
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    check_in: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    room_type: Mapped[str] = mapped_column(String(100), nullable=False)
    price_per_night_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    star_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="'{}'::jsonb",
    )

    def __repr__(self) -> str:
        return (
            f"<AccommodationModel id={self.id} "
            f"{self.name} {self.city} {self.check_in}→{self.check_out}>"
        )
