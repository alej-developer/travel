"""FastAPI application factory.

Call ``create_app()`` to get a fully hardened FastAPI instance.

Security layers (applied in order — outermost first):
  1. SecurityHeadersMiddleware — OWASP headers on every response
  2. RateLimitMiddleware       — Redis sliding-window rate limiting
  3. CORSMiddleware            — explicit allowlist, no wildcards

The factory pattern enables test overrides (custom settings, lifespan, etc.)
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from travel.config import get_settings
from travel.infrastructure.security.rate_limiter import RateLimitMiddleware
from travel.infrastructure.security.security_headers import SecurityHeadersMiddleware
from travel.presentation.api.v1.accommodations import router as accommodations_router
from travel.presentation.api.v1.flights import router as flights_router
from travel.presentation.api.v1.trains import router as trains_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup and shutdown events."""
    # Future: warm up connection pool, run startup checks, etc.
    yield
    # Future: dispose engine gracefully


def create_app() -> FastAPI:
    """Create and return a fully configured, security-hardened FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Travel Aggregation Engine",
        description=(
            "Aggregates flights, trains, and accommodation offers "
            "from multiple providers."
        ),
        version="0.1.0",
        # In production, disable docs unless explicitly enabled
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # Middleware stack
    # -----------------------------------------------------------------------
    # Note: Starlette middleware is applied in REVERSE order of registration.
    # The LAST registered middleware is the OUTERMOST wrapper.
    # Registration order below = execution order: SecurityHeaders → RateLimit → CORS

    # ── 1. CORS — innermost: only runs after rate limit passes ─────────────
    cors_origins = settings.cors_origins  # never contains '*'
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=bool(cors_origins),  # credentials only when origins are explicit
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID", "X-RateLimit-Policy", "Retry-After"],
        max_age=600,  # preflight cache: 10 minutes
    )

    # ── 2. Rate Limiting ───────────────────────────────────────────────────
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.redis_url,
    )

    # ── 3. Security Headers — outermost: wraps all responses ───────────────
    app.add_middleware(
        SecurityHeadersMiddleware,
        force_hsts=not settings.debug,  # only force HSTS in production
    )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    prefix = settings.api_v1_prefix
    app.include_router(flights_router, prefix=prefix)
    app.include_router(trains_router, prefix=prefix)
    app.include_router(accommodations_router, prefix=prefix)

    # -----------------------------------------------------------------------
    # Health check (no auth, no rate limit concern — simple liveness probe)
    # -----------------------------------------------------------------------
    @app.get(
        "/health",
        tags=["ops"],
        summary="Liveness probe",
        include_in_schema=False,  # hide from public OpenAPI docs
    )
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# ASGI entry-point used by uvicorn / gunicorn
app: FastAPI = create_app()
