"""FastAPI application factory.

Call ``create_app()`` to get a configured FastAPI instance. The factory pattern
allows easy test overrides (e.g. different settings or lifespan).
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from travel.config import get_settings
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
    """Create and return a fully configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Travel Aggregation Engine",
        description=(
            "Aggregates flights, trains, and accommodation offers "
            "from multiple providers."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # Middleware
    # -----------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    prefix = settings.api_v1_prefix
    app.include_router(flights_router, prefix=prefix)
    app.include_router(trains_router, prefix=prefix)
    app.include_router(accommodations_router, prefix=prefix)

    # -----------------------------------------------------------------------
    # Health check
    # -----------------------------------------------------------------------
    @app.get("/health", tags=["ops"], summary="Health check")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# ASGI entry-point used by uvicorn / gunicorn
app: FastAPI = create_app()
