"""Centralized dependency injection for FastAPI.

All database session dependencies must flow through this module.
Never create sessions directly in route handlers.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from travel.infrastructure.database.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """FastAPI dependency that yields a scoped AsyncSession.

    Usage in route handlers::

        @router.get("/")
        async def handler(db: DbSession) -> ...:
            result = await db.execute(...)

    The session is automatically committed on success and rolled back on error.
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


# Convenience type alias — use ``DbSession`` as a type annotation in handlers
DbSession = Annotated[AsyncSession, Depends(get_db)]
