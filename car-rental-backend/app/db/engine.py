"""Pula połączeń asyncpg (bez ORM).

Zamiast silnika SQLAlchemy używamy bezpośrednio sterownika ``asyncpg``.
Pula jest tworzona raz przy starcie procesu (``connect_db``) i zwalniana
przy zamknięciu (``close_db``). ``get_pool`` udostępnia ją zależnościom
FastAPI i bootstrapowi schematu.
"""

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    """Utwórz globalną pulę połączeń do PostgreSQL."""
    global _pool
    if _pool is not None:
        return
    _pool = await asyncpg.create_pool(
        dsn=settings.postgres_dsn,
        min_size=1,
        max_size=settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW,
        timeout=settings.DB_POOL_TIMEOUT,
        max_inactive_connection_lifetime=settings.DB_POOL_RECYCLE,
        command_timeout=60,
    )


async def close_db() -> None:
    """Zamknij pulę połączeń (shutdown aplikacji)."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Zwróć aktywną pulę; rzuć jeśli aplikacja nie wykonała ``connect_db``."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialized — call connect_db() first")
    return _pool
