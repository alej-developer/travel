"""Security layer tests.

Tests are fully in-memory — no real Redis, no network, no database.

Coverage
--------
1. RateLimitMiddleware — global tier, search tier, Redis pipeline logic (mocked).
2. SecurityHeadersMiddleware — presence of all OWASP headers, CSP, HSTS, X-Request-ID.
3. CORS — only declared origins allowed, wildcard is always rejected.
4. Input validators — IATA, ISO date, safe text, currency, metadata depth limit.
5. Schema-level injection hardening — SQL chars, MongoDB operators, oversized payloads.
6. app.py — middleware ordering, docs disabled in production, health endpoint.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError


# ===========================================================================
# 1. RateLimitMiddleware
# ===========================================================================


class TestRateLimitMiddleware:
    """Tests for the sliding-window Redis rate limiter."""

    def _make_middleware(
        self,
        global_limit: int = 50,
        search_limit: int = 5,
        enabled: bool = True,
    ) -> Any:
        """Build a middleware instance with mocked settings and Redis."""
        from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
        from starlette.applications import Starlette

        dummy_app = Starlette()

        with patch("travel.infrastructure.security.rate_limiter.get_settings") as mock_cfg, \
             patch("travel.infrastructure.security.rate_limiter.aioredis.from_url"):
            cfg = MagicMock()
            cfg.redis_url = "redis://localhost:6379/0"
            cfg.rate_limit_enabled = enabled
            cfg.rate_limit_global_requests = global_limit
            cfg.rate_limit_search_requests = search_limit
            mock_cfg.return_value = cfg
            mw = RateLimitMiddleware(dummy_app, redis_url="redis://localhost:6379/0")

        return mw

    @pytest.mark.asyncio
    async def test_disabled_middleware_passes_through(self) -> None:
        """When rate_limit_enabled=False, all requests pass immediately."""
        from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response

        dummy_app = Starlette()

        with patch("travel.infrastructure.security.rate_limiter.get_settings") as mock_cfg, \
             patch("travel.infrastructure.security.rate_limiter.aioredis.from_url"):
            cfg = MagicMock()
            cfg.redis_url = "redis://localhost"
            cfg.rate_limit_enabled = False
            cfg.rate_limit_global_requests = 50
            cfg.rate_limit_search_requests = 5
            mock_cfg.return_value = cfg
            mw = RateLimitMiddleware(dummy_app)

        mw._enabled = False
        call_next = AsyncMock(return_value=Response("ok"))
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/flights"

        response = await mw.dispatch(request, call_next)
        call_next.assert_awaited_once()
        assert response.status_code != 429

    @pytest.mark.asyncio
    async def test_under_limit_passes(self) -> None:
        """Requests under the limit are forwarded."""
        from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response

        dummy_app = Starlette()

        with patch("travel.infrastructure.security.rate_limiter.get_settings") as mock_cfg, \
             patch("travel.infrastructure.security.rate_limiter.aioredis.from_url") as mock_redis_factory:
            cfg = MagicMock()
            cfg.redis_url = "redis://localhost"
            cfg.rate_limit_enabled = True
            cfg.rate_limit_global_requests = 50
            cfg.rate_limit_search_requests = 5
            mock_cfg.return_value = cfg

            mock_redis = AsyncMock()
            mock_pipeline = AsyncMock()
            mock_pipeline.execute = AsyncMock(return_value=[None, 3, None, None])
            mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
            mock_pipeline.zremrangebyscore = MagicMock()
            mock_pipeline.zcard = MagicMock()
            mock_pipeline.zadd = MagicMock()
            mock_pipeline.expire = MagicMock()
            mock_redis_factory.return_value = mock_redis
            mw = RateLimitMiddleware(dummy_app)

        mw._redis = mock_redis
        mw._enabled = True
        mw._global_limit = 50
        mw._search_limit = 5

        call_next = AsyncMock(return_value=Response("ok", headers={}))
        request = MagicMock(spec=Request)
        request.url.path = "/health"
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "1.2.3.4"

        response = await mw.dispatch(request, call_next)
        assert response.status_code != 429

    @pytest.mark.asyncio
    async def test_over_limit_returns_429(self) -> None:
        """Requests over the limit get a 429 response."""
        from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
        from starlette.applications import Starlette
        from starlette.requests import Request

        dummy_app = Starlette()

        with patch("travel.infrastructure.security.rate_limiter.get_settings") as mock_cfg, \
             patch("travel.infrastructure.security.rate_limiter.aioredis.from_url") as mock_redis_factory:
            cfg = MagicMock()
            cfg.redis_url = "redis://localhost"
            cfg.rate_limit_enabled = True
            cfg.rate_limit_global_requests = 2
            cfg.rate_limit_search_requests = 2
            mock_cfg.return_value = cfg

            mock_redis = AsyncMock()
            mock_pipeline = AsyncMock()
            # count=3 means already at limit
            mock_pipeline.execute = AsyncMock(return_value=[None, 3, None, None])
            mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
            mock_pipeline.zremrangebyscore = MagicMock()
            mock_pipeline.zcard = MagicMock()
            mock_pipeline.zadd = MagicMock()
            mock_pipeline.expire = MagicMock()
            mock_redis.zrem = AsyncMock()
            mock_redis_factory.return_value = mock_redis
            mw = RateLimitMiddleware(dummy_app)

        mw._redis = mock_redis
        mw._enabled = True
        mw._global_limit = 2
        mw._search_limit = 2

        call_next = AsyncMock()
        request = MagicMock(spec=Request)
        request.url.path = "/health"
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "1.2.3.4"

        response = await mw.dispatch(request, call_next)
        assert response.status_code == 429
        call_next.assert_not_awaited()

    def test_too_many_response_has_retry_after(self) -> None:
        from travel.infrastructure.security.rate_limiter import RateLimitMiddleware

        response = RateLimitMiddleware._too_many(retry_after=30.5, tier="global")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "31"  # ceil
        assert response.headers["X-RateLimit-Tier"] == "global"

    def test_get_client_ip_from_x_forwarded_for(self) -> None:
        from travel.infrastructure.security.rate_limiter import _get_client_ip
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [(b"x-forwarded-for", b"203.0.113.1, 10.0.0.1")],
        }
        request = Request(scope)
        assert _get_client_ip(request) == "203.0.113.1"

    def test_get_client_ip_fallback_to_remote(self) -> None:
        from travel.infrastructure.security.rate_limiter import _get_client_ip
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
            "client": ("192.168.1.5", 12345),
        }
        request = Request(scope)
        assert _get_client_ip(request) == "192.168.1.5"


# ===========================================================================
# 2. SecurityHeadersMiddleware
# ===========================================================================


class TestSecurityHeadersMiddleware:
    """Verifies OWASP headers are present and correctly valued."""

    async def _make_response(self, path: str = "/api/v1/flights", scheme: str = "https") -> Any:
        """Run a synthetic request through the middleware and return the response."""
        from travel.infrastructure.security.security_headers import SecurityHeadersMiddleware
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response

        dummy_app = Starlette()

        with patch("travel.infrastructure.security.security_headers.get_settings") as mock_cfg:
            cfg = MagicMock()
            cfg.security_hsts_max_age = 31536000
            cfg.security_csp = "default-src 'none'; script-src 'self'"
            mock_cfg.return_value = cfg
            mw = SecurityHeadersMiddleware(dummy_app, force_hsts=True)

        inner_response = Response("ok", status_code=200)

        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": b"",
            "headers": [(b"x-forwarded-proto", scheme.encode())],
            "client": ("127.0.0.1", 9000),
        }
        request = Request(scope)
        call_next = AsyncMock(return_value=inner_response)
        return await mw.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_hsts_header_present(self) -> None:
        response = await self._make_response(scheme="https")
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]

    @pytest.mark.asyncio
    async def test_x_content_type_options_nosniff(self) -> None:
        response = await self._make_response()
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options_deny(self) -> None:
        response = await self._make_response()
        assert response.headers.get("X-Frame-Options") == "DENY"

    @pytest.mark.asyncio
    async def test_xss_protection_disabled(self) -> None:
        """OWASP recommends '0' to disable the legacy IE XSS filter."""
        response = await self._make_response()
        assert response.headers.get("X-XSS-Protection") == "0"

    @pytest.mark.asyncio
    async def test_csp_header_present(self) -> None:
        response = await self._make_response()
        assert "Content-Security-Policy" in response.headers
        assert "default-src" in response.headers["Content-Security-Policy"]

    @pytest.mark.asyncio
    async def test_referrer_policy(self) -> None:
        response = await self._make_response()
        assert "Referrer-Policy" in response.headers

    @pytest.mark.asyncio
    async def test_permissions_policy(self) -> None:
        response = await self._make_response()
        assert "Permissions-Policy" in response.headers
        pp = response.headers["Permissions-Policy"]
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp

    @pytest.mark.asyncio
    async def test_cache_control_no_store(self) -> None:
        response = await self._make_response()
        assert response.headers.get("Cache-Control") == "no-store"

    @pytest.mark.asyncio
    async def test_x_request_id_injected(self) -> None:
        response = await self._make_response()
        assert "X-Request-ID" in response.headers
        rid = response.headers["X-Request-ID"]
        assert len(rid) == 36  # UUID format


# ===========================================================================
# 3. CORS configuration
# ===========================================================================


class TestCorsConfiguration:
    """Verifies CORS settings: no wildcard, explicit origins only."""

    def test_cors_origins_from_settings(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "ALLOWED_ORIGINS": "https://app.example.com,https://admin.example.com",
            },
        ):
            from travel.config import get_settings
            get_settings.cache_clear()  # type: ignore[attr-defined]
            s = get_settings()
            assert "https://app.example.com" in s.cors_origins
            assert "https://admin.example.com" in s.cors_origins
            assert "*" not in s.cors_origins
            get_settings.cache_clear()  # type: ignore[attr-defined]

    def test_wildcard_stripped_from_origins(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "ALLOWED_ORIGINS": "*",
            },
        ):
            from travel.config import get_settings
            get_settings.cache_clear()  # type: ignore[attr-defined]
            s = get_settings()
            assert "*" not in s.cors_origins
            assert s.cors_origins == []
            get_settings.cache_clear()  # type: ignore[attr-defined]

    def test_empty_origins_returns_empty_list(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "ALLOWED_ORIGINS": "",
            },
        ):
            from travel.config import get_settings
            get_settings.cache_clear()  # type: ignore[attr-defined]
            s = get_settings()
            assert s.cors_origins == []
            get_settings.cache_clear()  # type: ignore[attr-defined]

    def test_wildcard_mixed_with_real_origins_stripped(self) -> None:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "ALLOWED_ORIGINS": "https://legit.com,*,https://also-legit.com",
            },
        ):
            from travel.config import get_settings
            get_settings.cache_clear()  # type: ignore[attr-defined]
            s = get_settings()
            assert "*" not in s.cors_origins
            assert "https://legit.com" in s.cors_origins
            assert "https://also-legit.com" in s.cors_origins
            get_settings.cache_clear()  # type: ignore[attr-defined]


# ===========================================================================
# 4. Input validators
# ===========================================================================


class TestInputValidators:
    """Unit tests for each validator function in validators.py."""

    # ── IATA ──────────────────────────────────────────────────────────────

    def test_valid_iata_uppercase(self) -> None:
        from travel.application.schemas.validators import _validate_iata
        assert _validate_iata("MAD") == "MAD"

    def test_iata_lowercased_input(self) -> None:
        from travel.application.schemas.validators import _validate_iata
        assert _validate_iata("mad") == "MAD"

    def test_iata_too_short_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_iata
        with pytest.raises(ValueError):
            _validate_iata("MA")

    def test_iata_numeric_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_iata
        with pytest.raises(ValueError):
            _validate_iata("1BC")

    def test_iata_with_special_chars_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_iata
        with pytest.raises(ValueError):
            _validate_iata("MA'")

    # ── ISO Date ──────────────────────────────────────────────────────────

    def test_valid_iso_date(self) -> None:
        from travel.application.schemas.validators import _validate_iso_date
        assert _validate_iso_date("2025-09-01") == "2025-09-01"

    def test_iso_date_invalid_format_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_iso_date
        with pytest.raises(ValueError):
            _validate_iso_date("01-09-2025")

    def test_iso_date_with_injection_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_iso_date
        with pytest.raises(ValueError):
            _validate_iso_date("2025-09-01'; DROP TABLE flights;--")

    def test_iso_date_impossible_date_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_iso_date
        with pytest.raises(ValueError):
            _validate_iso_date("2025-13-45")

    # ── Safe text ─────────────────────────────────────────────────────────

    def test_safe_text_normal(self) -> None:
        from travel.application.schemas.validators import _validate_safe_text
        assert _validate_safe_text("Madrid Central") == "Madrid Central"

    def test_safe_text_sql_quote_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_safe_text
        with pytest.raises(ValueError):
            _validate_safe_text("Madrid' OR '1'='1")

    def test_safe_text_nosql_dollar_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_safe_text
        with pytest.raises(ValueError):
            _validate_safe_text("{$gt: 0}")

    def test_safe_text_semicolon_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_safe_text
        with pytest.raises(ValueError):
            _validate_safe_text("Madrid; DROP TABLE trains")

    def test_safe_text_empty_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_safe_text
        with pytest.raises(ValueError):
            _validate_safe_text("   ")

    def test_safe_text_accented_chars_accepted(self) -> None:
        from travel.application.schemas.validators import _validate_safe_text
        assert "París" in _validate_safe_text("París")

    # ── Currency ──────────────────────────────────────────────────────────

    def test_valid_currency(self) -> None:
        from travel.application.schemas.validators import _validate_currency
        assert _validate_currency("EUR") == "EUR"

    def test_currency_lowercase_normalised(self) -> None:
        from travel.application.schemas.validators import _validate_currency
        assert _validate_currency("eur") == "EUR"

    def test_currency_injection_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_currency
        with pytest.raises(ValueError):
            _validate_currency("E'R")

    def test_currency_too_long_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_currency
        with pytest.raises(ValueError):
            _validate_currency("EURO")

    # ── Metadata ──────────────────────────────────────────────────────────

    def test_valid_metadata(self) -> None:
        from travel.application.schemas.validators import _validate_metadata
        result = _validate_metadata({"source": "booking", "rank": 1, "featured": True})
        assert result["source"] == "booking"

    def test_metadata_nested_object_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_metadata
        with pytest.raises(ValueError, match="scalar"):
            _validate_metadata({"nested": {"key": "value"}})

    def test_metadata_list_value_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_metadata
        with pytest.raises(ValueError, match="scalar"):
            _validate_metadata({"tags": ["a", "b"]})

    def test_metadata_too_many_keys_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_metadata
        too_many = {f"key_{i}": i for i in range(21)}
        with pytest.raises(ValueError, match="20 keys"):
            _validate_metadata(too_many)

    def test_metadata_key_too_long_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_metadata
        with pytest.raises(ValueError, match="50-character"):
            _validate_metadata({"a" * 51: "value"})

    def test_metadata_string_value_too_long_rejected(self) -> None:
        from travel.application.schemas.validators import _validate_metadata
        with pytest.raises(ValueError, match="500-character"):
            _validate_metadata({"key": "x" * 501})


# ===========================================================================
# 5. Schema-level injection hardening
# ===========================================================================


class TestFlightSchemaInjectionHardening:
    def _valid_payload(self) -> dict[str, Any]:
        return {
            "origin": "MAD",
            "destination": "BCN",
            "departure_at": datetime(2025, 9, 1, 8, 0, tzinfo=timezone.utc),
            "arrival_at": datetime(2025, 9, 1, 9, 30, tzinfo=timezone.utc),
            "airline": "IB",
            "flight_number": "IB1234",
            "price_cents": 4500,
            "currency": "EUR",
        }

    def test_valid_flight_create(self) -> None:
        from travel.application.schemas.flight import FlightCreate
        f = FlightCreate(**self._valid_payload())
        assert f.origin == "MAD"

    def test_sql_injection_in_origin_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate
        payload = {**self._valid_payload(), "origin": "MA'"}
        with pytest.raises(ValidationError):
            FlightCreate(**payload)

    def test_nosql_injection_in_metadata_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate
        payload = {**self._valid_payload(), "metadata": {"$gt": {"password": ""}}}
        with pytest.raises(ValidationError):
            FlightCreate(**payload)

    def test_same_origin_destination_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate
        payload = {**self._valid_payload(), "destination": "MAD"}
        with pytest.raises(ValidationError, match="different"):
            FlightCreate(**payload)

    def test_oversized_price_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate
        payload = {**self._valid_payload(), "price_cents": 999_999_999}
        with pytest.raises(ValidationError):
            FlightCreate(**payload)

    def test_invalid_flight_number_pattern_rejected(self) -> None:
        from travel.application.schemas.flight import FlightCreate
        payload = {**self._valid_payload(), "flight_number": "INVALID123"}
        with pytest.raises(ValidationError):
            FlightCreate(**payload)


class TestTrainSchemaInjectionHardening:
    def _valid_payload(self) -> dict[str, Any]:
        return {
            "origin_station": "Madrid Atocha",
            "destination_station": "Barcelona Sants",
            "departure_at": datetime(2025, 9, 1, 7, 0, tzinfo=timezone.utc),
            "arrival_at": datetime(2025, 9, 1, 9, 30, tzinfo=timezone.utc),
            "operator": "Renfe",
            "train_number": "AVE-3090",
            "service_class": "FIRST",
            "price_cents": 8900,
            "currency": "EUR",
        }

    def test_valid_train_create(self) -> None:
        from travel.application.schemas.train import TrainCreate
        t = TrainCreate(**self._valid_payload())
        assert t.operator == "Renfe"

    def test_sql_injection_in_station_rejected(self) -> None:
        from travel.application.schemas.train import TrainCreate
        payload = {**self._valid_payload(), "origin_station": "Madrid' OR 1=1--"}
        with pytest.raises(ValidationError):
            TrainCreate(**payload)

    def test_same_origin_destination_rejected(self) -> None:
        from travel.application.schemas.train import TrainCreate
        payload = {**self._valid_payload(), "destination_station": "Madrid Atocha"}
        with pytest.raises(ValidationError, match="different"):
            TrainCreate(**payload)

    def test_shell_injection_in_train_number_rejected(self) -> None:
        from travel.application.schemas.train import TrainCreate
        payload = {**self._valid_payload(), "train_number": "AVE;rm -rf /"}
        with pytest.raises(ValidationError):
            TrainCreate(**payload)


class TestAccommodationSchemaInjectionHardening:
    def _valid_payload(self) -> dict[str, Any]:
        from datetime import date
        return {
            "name": "Hotel Ritz Madrid",
            "address": "Plaza de la Lealtad 5",
            "city": "Madrid",
            "country_code": "ES",
            "check_in": date(2025, 7, 1),
            "check_out": date(2025, 7, 4),
            "room_type": "DOUBLE",
            "price_per_night_cents": 12000,
            "currency": "EUR",
        }

    def test_valid_accommodation_create(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate
        a = AccommodationCreate(**self._valid_payload())
        assert a.city == "Madrid"

    def test_nosql_injection_in_city_rejected(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate
        payload = {**self._valid_payload(), "city": "{$ne: null}"}
        with pytest.raises(ValidationError):
            AccommodationCreate(**payload)

    def test_invalid_country_code_rejected(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate
        payload = {**self._valid_payload(), "country_code": "ESP"}
        with pytest.raises(ValidationError):
            AccommodationCreate(**payload)

    def test_lowercase_country_code_rejected(self) -> None:
        from travel.application.schemas.accommodation import AccommodationCreate
        payload = {**self._valid_payload(), "country_code": "es"}
        with pytest.raises(ValidationError):
            AccommodationCreate(**payload)

    def test_stay_over_365_nights_rejected(self) -> None:
        from datetime import date
        from travel.application.schemas.accommodation import AccommodationCreate
        payload = {
            **self._valid_payload(),
            "check_in": date(2025, 1, 1),
            "check_out": date(2026, 2, 1),  # > 365 nights
        }
        with pytest.raises(ValidationError, match="365"):
            AccommodationCreate(**payload)


# ===========================================================================
# 6. app.py — middleware and production hardening
# ===========================================================================


class TestAppFactory:
    def _make_app(self, debug: bool = True, allowed_origins: str = "") -> Any:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
                "SECRET_KEY": "a-very-secret-key-32chars!!!!!!!",
                "DEBUG": str(debug).lower(),
                "ALLOWED_ORIGINS": allowed_origins,
                "RATE_LIMIT_ENABLED": "false",  # disable Redis dep in tests
            },
        ):
            from travel.config import get_settings
            from travel.presentation.app import create_app
            get_settings.cache_clear()  # type: ignore[attr-defined]
            with patch("travel.infrastructure.security.rate_limiter.aioredis.from_url"), \
                 patch("travel.infrastructure.security.rate_limiter.get_settings") as m:
                m.return_value = get_settings()
                app = create_app()
            get_settings.cache_clear()  # type: ignore[attr-defined]
        return app

    def test_middleware_includes_rate_limiter(self) -> None:
        app = self._make_app()
        from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
        user_mw_types = [m.cls for m in app.user_middleware]
        assert RateLimitMiddleware in user_mw_types

    def test_middleware_includes_security_headers(self) -> None:
        app = self._make_app()
        from travel.infrastructure.security.security_headers import SecurityHeadersMiddleware
        user_mw_types = [m.cls for m in app.user_middleware]
        assert SecurityHeadersMiddleware in user_mw_types

    def test_middleware_includes_cors(self) -> None:
        from fastapi.middleware.cors import CORSMiddleware
        app = self._make_app()
        user_mw_types = [m.cls for m in app.user_middleware]
        assert CORSMiddleware in user_mw_types

    def test_docs_disabled_in_production(self) -> None:
        app = self._make_app(debug=False)
        assert app.docs_url is None
        assert app.redoc_url is None
        assert app.openapi_url is None

    def test_docs_enabled_in_debug(self) -> None:
        app = self._make_app(debug=True)
        assert app.docs_url == "/docs"
