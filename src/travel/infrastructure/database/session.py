"""Async SQLAlchemy engine and session factory.

This module owns the *single* AsyncEngine and AsyncSessionLocal factory.
Never import these directly from other layers — use the dependency injection
system in ``travel.presentation.dependencies`` instead.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from travel.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Engine & session factory (module-level singletons)
# ---------------------------------------------------------------------------


def build_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create and return an AsyncEngine from settings.

    Separating engine creation into a function enables easy overriding in tests
    (pass a test-specific Settings with a test DB URL).
    """
    cfg = settings or get_settings()
    return create_async_engine(
        str(cfg.database_url),
        pool_size=cfg.db_pool_size,
        max_overflow=cfg.db_max_overflow,
        pool_timeout=cfg.db_pool_timeout,
        echo=cfg.db_echo,
        # asyncpg returns native UUIDs; let SQLAlchemy handle the casting
        json_serializer=lambda obj: __import__("json").dumps(obj, default=str),
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async_sessionmaker bound to *engine*."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


# Module-level singletons — created LAZILY on first access so that importing
# this module in tests without a DATABASE_URL does not raise ValidationError.
# Call get_engine() / get_session_factory() instead of accessing these directly.

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the module-level AsyncEngine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the module-level session factory, creating it on first call."""
    global _session_factory
    if _session_factory is None:
        _session_factory = build_session_factory(get_engine())
    return _session_factory


# Legacy aliases kept for backward compatibility with existing imports.
# Accessing these properties triggers lazy initialisation.
class _LazyEngine:
    """Transparent proxy so ``engine.xxx`` still works after lazy init."""

    def __getattr__(self, name: str) -> object:
        return getattr(get_engine(), name)


class _LazySessionLocal:
    """Transparent proxy so ``AsyncSessionLocal()`` still works."""

    def __call__(self, **kwargs: object) -> object:
        return get_session_factory()(**kwargs)  # type: ignore[operator]

    def __getattr__(self, name: str) -> object:
        return getattr(get_session_factory(), name)


engine: Any = _LazyEngine()
AsyncSessionLocal: Any = _LazySessionLocal()


# ---------------------------------------------------------------------------
# Context-manager helper (for scripts / CLI / testing)
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, Any]:
    """Yield an AsyncSession with automatic rollback on error.

    This is the canonical async context manager for obtaining a session.
    FastAPI dependency injection wraps this in ``presentation.dependencies``.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
