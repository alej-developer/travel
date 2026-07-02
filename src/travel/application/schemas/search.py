"""Pydantic v2 schemas for aggregated search — request/response DTOs."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from travel.application.schemas.validators import SafeStationName


class TransportType(str, Enum):
    """Supported transport types."""

    FLIGHT = "flight"
    TRAIN = "train"
    ACCOMMODATION = "accommodation"


class SearchRequest(BaseModel):
    """Validated search parameters for the aggregated search endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    origin: SafeStationName = Field(
        ..., description="Origin city or station name"
    )
    destination: SafeStationName = Field(
        ..., description="Destination city or station name"
    )
    date_from: date = Field(
        ..., description="Departure or check-in date"
    )
    date_to: date | None = Field(
        default=None, description="Return or check-out date"
    )
    passengers: int = Field(
        default=1, ge=1, le=9, description="Number of passengers/adults"
    )
    transport_type: TransportType = Field(
        default=TransportType.FLIGHT, description="Type of transport to search"
    )

    @model_validator(mode="after")
    def date_to_after_date_from(self) -> "SearchRequest":
        if self.date_to and self.date_to <= self.date_from:
            raise ValueError("date_to must be after date_from")
        return self

    @model_validator(mode="after")
    def date_from_not_in_past(self) -> "SearchRequest":
        if self.date_from < date.today():
            raise ValueError("date_from cannot be in the past")
        return self


class ProviderResult(BaseModel):
    """A single result from one provider."""

    model_config = ConfigDict(populate_by_name=True)

    provider: str = Field(
        ..., description="Provider domain (e.g. booking.com, renfe.com)"
    )
    provider_display_name: str = Field(
        ..., description="Human-readable provider name"
    )
    price_raw: str | None = Field(
        default=None, description="Raw price string as scraped"
    )
    price_cents: int | None = Field(
        default=None, description="Normalised price in cents (if parseable)"
    )
    currency: str = Field(
        default="EUR", description="ISO 4217 currency code"
    )
    departure_time: str | None = Field(
        default=None, description="Departure or check-in time/date"
    )
    arrival_time: str | None = Field(
        default=None, description="Arrival or check-out time/date"
    )
    duration: str | None = Field(
        default=None, description="Journey duration"
    )
    name: str | None = Field(
        default=None, description="Property/route name"
    )
    operator: str | None = Field(
        default=None, description="Train operator or airline name"
    )
    extra: dict[str, object] = Field(
        default_factory=dict, description="Additional provider-specific data"
    )
    url: str | None = Field(
        default=None, description="Direct link to the provider's offer"
    )


class AggregatedSearchResponse(BaseModel):
    """Aggregated search response with results from all matching providers."""

    model_config = ConfigDict(populate_by_name=True)

    transport_type: TransportType
    origin: str
    destination: str
    date_from: str
    date_to: str | None
    providers_queried: list[str] = Field(
        ..., description="List of provider domains that were scraped"
    )
    providers_succeeded: list[str] = Field(
        default_factory=list, description="Providers that returned results"
    )
    providers_failed: list[str] = Field(
        default_factory=list, description="Providers that failed or returned errors"
    )
    results: list[ProviderResult] = Field(
        default_factory=list, description="All results sorted by price ascending"
    )
    total_results: int = Field(
        default=0, description="Total number of results across all providers"
    )
    search_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of when the search was executed",
    )


# ── Provider display names ──────────────────────────────────────────────────

PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    # Trains
    "renfe.com": "Renfe",
    "trenes.com": "Trenes.com",
    "sncf-connect.com": "SNCF Connect",
    "thetrainline.com": "Trainline",
    "ouigo.com": "Ouigo",
    "iryo.eu": "Iryo",
    # Flights
    "iberia.com": "Iberia",
    "ryanair.com": "Ryanair",
    "vueling.com": "Vueling",
    "easyjet.com": "EasyJet",
    "skyscanner.es": "Skyscanner",
    "google.com/travel/flights": "Google Flights",
    # Accommodations
    "booking.com": "Booking.com",
    "airbnb.com": "Airbnb",
    "vrbo.com": "Vrbo",
    "ruralia.com": "Ruralia",
    "escapadarural.com": "Escapada Rural",
    "idealista.com": "Idealista",
    "trivago.es": "Trivago",
}
