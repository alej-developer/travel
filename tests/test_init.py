"""Initialization smoke tests.

These tests verify that:
1. All modules import correctly (no missing dependencies, circular imports, etc.)
2. Domain entities instantiate and compute derived values correctly.
3. Pydantic v2 schemas validate correctly and reject invalid data.
4. SQLAlchemy engine can be built from a synthetic URL (no real DB needed).
5. FastAPI app factory returns a valid application instance.
6. Dependency injection wiring is correct.

No real database connection is required — these are pure smoke/unit tests.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# 1. Domain entity imports and logic
# ---------------------------------------------------------------------------


class TestFlightEntity:
    def test_import(self) -> None:
        from travel.domain.entities.flight import FlightEntity  # noqa: F401

    def test_duration_minutes(self) -> None:
        from travel.domain.entities.flight import FlightEntity

        flight = FlightEntity(
            origin="MAD",
            destination="BCN",
            departure_at=datetime(2025, 6, 1, 8, 0, tzinfo=timezone.utc),
            arrival_at=datetime(2025, 6, 1, 9, 30, tzinfo=timezone.utc),
            airline="IB",
            flight_number="IB1234",
            price_cents=4500,
            currency="EUR",
        )
        assert flight.duration_minutes() == 90


class TestTrainEntity:
    def test_import(self) -> None:
        from travel.domain.entities.train import TrainEntity  # noqa: F401

    def test_duration_minutes(self) -> None:
        from travel.domain.entities.train import TrainEntity

        train = TrainEntity(
            origin_station="Madrid Atocha",
            destination_station="Barcelona Sants",
            departure_at=datetime(2025, 6, 1, 7, 0, tzinfo=timezone.utc),
            arrival_at=datetime(2025, 6, 1, 9, 30, tzinfo=timezone.utc),
            operator="Renfe",
            train_number="AVE-3090",
            service_class="FIRST",
            price_cents=8900,
            currency="EUR",
        )
        assert train.duration_minutes() == 150


class TestAccommodationEntity:
    def test_import(self) -> None:
        from travel.domain.entities.accommodation import AccommodationEntity  # noqa: F401

    def test_total_nights_and_price(self) -> None:
        from travel.domain.entities.accommodation import AccommodationEntity

        acc = AccommodationEntity(
            name="Hotel Test",
            address="Calle Test 1",
            city="Madrid",
            country_code="ES",
            check_in=date(2025, 7, 1),
            check_out=date(2025, 7, 4),
            room_type="DOUBLE",
            price_per_night_cents=12000,
            currency="EUR",
        )
        assert acc.total_nights() == 3
        assert acc.total_price_cents() == 36000


# ---------------------------------------------------------------------------
# 2. Pydantic v2 schema validation
# ---------------------------------------------------------------------------


class TestFlightSchemas:
    def test_valid_create(self) -> None:
        from travel.application.schemas.flight import FlightCreate

        schema = FlightCreate(
            origin="MAD",
            destination="BCN",
            departure_at=datetime(2025, 6, 1, 8, 0, tzinfo=timezone.utc),
            arrival_at=datetime(2025, 6, 1, 9, 30, tzinfo=timezone.utc),
            airline="IB",
            flight_number="IB1234",
            price_cents=4500,
            currency="EUR",
        )
        assert schema.origin == "MAD"

    def test_arrival_before_departure_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate

        with pytest.raises(ValidationError):
            FlightCreate(
                origin="MAD",
                destination="BCN",
                departure_at=datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
                arrival_at=datetime(2025, 6, 1, 8, 0, tzinfo=timezone.utc),
                airline="IB",
                flight_number="IB1234",
                price_cents=4500,
                currency="EUR",
            )

    def test_negative_price_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate

        with pytest.raises(ValidationError):
            FlightCreate(
                origin="MAD",
                destination="BCN",
                departure_at=datetime(2025, 6, 1, 8, 0, tzinfo=timezone.utc),
                arrival_at=datetime(2025, 6, 1, 9, 0, tzinfo=timezone.utc),
                airline="IB",
                flight_number="IB1234",
                price_cents=-100,
                currency="EUR",
            )


class TestTrainSchemas:
    def test_valid_create(self) -> None:
        from travel.application.schemas.train import TrainCreate

        schema = TrainCreate(
            origin_station="Madrid Atocha",
            destination_station="Barcelona Sants",
            departure_at=datetime(2025, 6, 1, 7, 0, tzinfo=timezone.utc),
            arrival_at=datetime(2025, 6, 1, 9, 30, tzinfo=timezone.utc),
            operator="Renfe",
            train_number="AVE-3090",
            service_class="FIRST",
            price_cents=8900,
            currency="EUR",
        )
        assert schema.service_class == "FIRST"


class TestAccommodationSchemas:
    def test_valid_create(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate

        schema = AccommodationCreate(
            name="Hotel Test",
            address="Calle Test 1",
            city="Madrid",
            country_code="ES",
            check_in=date(2025, 7, 1),
            check_out=date(2025, 7, 4),
            room_type="DOUBLE",
            price_per_night_cents=12000,
            currency="EUR",
            star_rating=4,
        )
        assert schema.star_rating == 4

    def test_checkout_before_checkin_rejected(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate

        with pytest.raises(ValidationError):
            AccommodationCreate(
                name="Hotel Test",
                address="Calle Test 1",
                city="Madrid",
                country_code="ES",
                check_in=date(2025, 7, 5),
                check_out=date(2025, 7, 1),
                room_type="DOUBLE",
                price_per_night_cents=12000,
                currency="EUR",
            )

    def test_star_rating_out_of_range_rejected(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate

        with pytest.raises(ValidationError):
            AccommodationCreate(
                name="Hotel Test",
                address="Calle Test 1",
                city="Madrid",
                country_code="ES",
                check_in=date(2025, 7, 1),
                check_out=date(2025, 7, 4),
                room_type="DOUBLE",
                price_per_night_cents=12000,
                currency="EUR",
                star_rating=6,  # invalid: max is 5
            )


# ---------------------------------------------------------------------------
# 3. SQLAlchemy Base and model imports
# ---------------------------------------------------------------------------


class TestOrmModels:
    def test_base_import(self) -> None:
        from travel.infrastructure.database.base import Base  # noqa: F401

    def test_flight_model_import(self) -> None:
        from travel.infrastructure.models.flight import FlightModel  # noqa: F401

    def test_train_model_import(self) -> None:
        from travel.infrastructure.models.train import TrainModel  # noqa: F401

    def test_accommodation_model_import(self) -> None:
        from travel.infrastructure.models.accommodation import (  # noqa: F401
            AccommodationModel,
        )

    def test_all_tables_registered(self) -> None:
        """Verify that Alembic will see all tables via Base.metadata."""
        import travel.infrastructure.models.accommodation  # noqa: F401
        import travel.infrastructure.models.flight  # noqa: F401
        import travel.infrastructure.models.train  # noqa: F401
        from travel.infrastructure.database.base import Base

        table_names = set(Base.metadata.tables.keys())
        assert "flights" in table_names
        assert "trains" in table_names
        assert "accommodations" in table_names


# ---------------------------------------------------------------------------
# 4. Engine builder (no real DB connection)
# ---------------------------------------------------------------------------


class TestEngineBuilder:
    def test_build_engine_with_valid_url(self) -> None:
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb"},
            clear=False,
        ):
            from travel.config import Settings, get_settings
            from travel.infrastructure.database.session import build_engine

            get_settings.cache_clear()  # type: ignore[attr-defined]
            settings = Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",  # type: ignore[arg-type]
                secret_key="a-very-secret-key-32chars!!!!!!!",
            )
            engine = build_engine(settings)
            assert engine is not None
            assert "asyncpg" in str(engine.url)
            get_settings.cache_clear()  # type: ignore[attr-defined]

    def test_build_session_factory(self) -> None:
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb"},
            clear=False,
        ):
            from travel.config import Settings, get_settings
            from travel.infrastructure.database.session import (
                build_engine,
                build_session_factory,
            )

            get_settings.cache_clear()  # type: ignore[attr-defined]
            settings = Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",  # type: ignore[arg-type]
                secret_key="a-very-secret-key-32chars!!!!!!!",
            )
            engine = build_engine(settings)
            factory = build_session_factory(engine)
            assert factory is not None
            get_settings.cache_clear()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 5. FastAPI app factory
# ---------------------------------------------------------------------------


class TestAppFactory:
    def test_create_app_returns_fastapi_instance(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "DEBUG": "true",
                "RATE_LIMIT_ENABLED": "false",
            },
        ):
            from travel.config import get_settings
            from travel.presentation.app import create_app

            get_settings.cache_clear()  # type: ignore[attr-defined]
            app = create_app()
            assert app is not None
            assert app.title == "Travel Aggregation Engine"

    def test_health_endpoint(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "DEBUG": "true",
                "RATE_LIMIT_ENABLED": "false",
            },
        ):
            from travel.config import get_settings
            from travel.presentation.app import create_app

            get_settings.cache_clear()  # type: ignore[attr-defined]
            app = create_app()
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    def test_openapi_schema_has_all_routers(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "DEBUG": "true",
                "RATE_LIMIT_ENABLED": "false",
            },
        ):
            from travel.config import get_settings
            from travel.presentation.app import create_app

            get_settings.cache_clear()  # type: ignore[attr-defined]
            app = create_app()
            schema = app.openapi()
            paths = schema["paths"]
            assert any("flights" in p for p in paths)
            assert any("trains" in p for p in paths)
            assert any("accommodations" in p for p in paths)


# ---------------------------------------------------------------------------
# 6. Settings validation
# ---------------------------------------------------------------------------


class TestSettings:
    def test_non_asyncpg_url_rejected(self) -> None:
        from travel.config import Settings

        with pytest.raises(Exception):
            Settings(
                database_url="postgresql+psycopg2://user:pass@localhost:5432/db",  # type: ignore[arg-type]
                secret_key="a-very-secret-key-32chars!!!!!!!",
            )

    def test_valid_settings(self) -> None:
        from travel.config import Settings

        s = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",  # type: ignore[arg-type]
            secret_key="a-very-secret-key-32chars!!!!!!!",
        )
        assert s.environment == "development"
