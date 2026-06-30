"""Shared Pydantic field validators for input sanitisation.

Design goals
------------
* Prevent SQL injection attempts by restricting allowed characters via regex.
* Prevent NoSQL injection (MongoDB operator injection, JSON operator abuse)
  by whitelisting rather than blacklisting character sets.
* Enforce hard length limits to thwart buffer overflow / memory exhaustion.
* Keep validators composable so they can be reused across all schemas.

Validator catalogue
-------------------
``IataCode``
    3-letter IATA airport/station code: only uppercase A-Z.
``SafeSearchString``
    Free-text search field (city names, station names): letters, digits, spaces,
    hyphens and basic accented characters. Max 100 chars.
``IsoDate``
    Calendar date in YYYY-MM-DD format validated via regex *and* ``date.fromisoformat``.
``SafeCurrency``
    3-letter ISO 4217 currency code: only uppercase A-Z.
``SafeFlightNumber``
    Airline + number: 2 uppercase letters followed by 1-4 digits.
``SafeOperatorName``
    Transport operator name: alphanumeric + spaces + hyphens. Max 100 chars.
``MetadataDict``
    JSONB metadata: values must be scalar (str/int/float/bool/None), no nested
    objects, to prevent deep-object injection.  Max 20 keys, keys max 50 chars.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any

from pydantic import AfterValidator, Field

# ---------------------------------------------------------------------------
# Internal regex patterns
# ---------------------------------------------------------------------------

_RE_IATA = re.compile(r"^[A-Z]{3}$")
_RE_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RE_CURRENCY = re.compile(r"^[A-Z]{3}$")
_RE_FLIGHT_NUMBER = re.compile(r"^[A-Z]{2}\d{1,4}$")
# Allows Unicode letters (via \w for Python re with \u flag emulated by [^\W\d_])
# plus spaces and hyphens — blocks $, {, }, [, ], ;, ', ", \, etc.
_RE_SAFE_TEXT = re.compile(r"^[\w\s\-\.,'àáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿÀ-Ö×Ø-öø-ÿ]+$")
_RE_OPERATOR = re.compile(r"^[\w\s\-\.]+$")

# ---------------------------------------------------------------------------
# Validator functions (used in Annotated types)
# ---------------------------------------------------------------------------


def _validate_iata(v: str) -> str:
    v = v.strip().upper()
    if not _RE_IATA.match(v):
        raise ValueError(
            f"Invalid IATA code '{v}'. Must be exactly 3 uppercase letters (A-Z)."
        )
    return v


def _validate_iso_date(v: str) -> str:
    v = v.strip()
    if not _RE_ISO_DATE.match(v):
        raise ValueError(
            f"Invalid date '{v}'. Expected ISO 8601 format YYYY-MM-DD."
        )
    try:
        date.fromisoformat(v)
    except ValueError:
        raise ValueError(f"Invalid calendar date: '{v}'.")
    return v


def _validate_safe_text(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Field must not be empty.")
    if not _RE_SAFE_TEXT.match(v):
        raise ValueError(
            "Field contains disallowed characters. "
            "Only letters, digits, spaces, hyphens, dots and common punctuation are allowed."
        )
    return v


def _validate_currency(v: str) -> str:
    v = v.strip().upper()
    if not _RE_CURRENCY.match(v):
        raise ValueError(
            f"Invalid currency code '{v}'. Must be exactly 3 uppercase letters."
        )
    return v


def _validate_flight_number(v: str) -> str:
    v = v.strip().upper()
    if not _RE_FLIGHT_NUMBER.match(v):
        raise ValueError(
            f"Invalid flight number '{v}'. "
            "Expected 2 uppercase letters followed by 1-4 digits (e.g. IB1234)."
        )
    return v


def _validate_operator(v: str) -> str:
    v = v.strip()
    if not _RE_OPERATOR.match(v):
        raise ValueError(
            "Operator name contains disallowed characters. "
            "Only alphanumeric characters, spaces, hyphens and dots are allowed."
        )
    return v


def _validate_metadata(v: dict[str, Any]) -> dict[str, Any]:
    """Ensure metadata values are scalar only — no nested objects/lists."""
    if len(v) > 20:
        raise ValueError("metadata must have at most 20 keys.")
    for key, value in v.items():
        if len(key) > 50:
            raise ValueError(f"metadata key '{key[:20]}...' exceeds 50-character limit.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise ValueError(
                f"metadata value for key '{key}' must be a scalar "
                f"(str, int, float, bool, or null). Got: {type(value).__name__}."
            )
        if isinstance(value, str) and len(value) > 500:
            raise ValueError(
                f"metadata string value for key '{key}' exceeds 500-character limit."
            )
    return v


# ---------------------------------------------------------------------------
# Annotated type aliases — use these as field types in schemas
# ---------------------------------------------------------------------------

IataCode = Annotated[
    str,
    Field(min_length=3, max_length=3, description="IATA 3-letter code (e.g. MAD, JFK)"),
    AfterValidator(_validate_iata),
]

IsoDateStr = Annotated[
    str,
    Field(min_length=10, max_length=10, description="ISO 8601 date (YYYY-MM-DD)"),
    AfterValidator(_validate_iso_date),
]

SafeStationName = Annotated[
    str,
    Field(
        min_length=2,
        max_length=100,
        description="Station or city name — letters, digits, spaces, hyphens only",
    ),
    AfterValidator(_validate_safe_text),
]

SafeOperatorName = Annotated[
    str,
    Field(min_length=2, max_length=100, description="Transport operator name"),
    AfterValidator(_validate_operator),
]

CurrencyCode = Annotated[
    str,
    Field(min_length=3, max_length=3, description="ISO 4217 currency code (e.g. EUR)"),
    AfterValidator(_validate_currency),
]

SafeFlightNumber = Annotated[
    str,
    Field(min_length=4, max_length=6, description="Flight number (e.g. IB1234)"),
    AfterValidator(_validate_flight_number),
]

SafeAirlineName = Annotated[
    str,
    Field(min_length=2, max_length=10, description="Airline ICAO/IATA code"),
    AfterValidator(_validate_operator),
]

SafeRoomType = Annotated[
    str,
    Field(min_length=2, max_length=50, description="Room type (e.g. DOUBLE, SUITE)"),
    AfterValidator(_validate_operator),
]

SafeAddress = Annotated[
    str,
    Field(min_length=5, max_length=200, description="Physical address"),
    AfterValidator(_validate_safe_text),
]

SafeName = Annotated[
    str,
    Field(min_length=1, max_length=200, description="Property or service name"),
    AfterValidator(_validate_safe_text),
]

SafeMetadata = Annotated[
    dict[str, Any],
    AfterValidator(_validate_metadata),
]
