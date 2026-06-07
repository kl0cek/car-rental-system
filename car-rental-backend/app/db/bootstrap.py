"""Zastosowanie schematu relacyjnego przy starcie aplikacji.

W wersji bez ORM/Alembica schemat trzymamy w jawnym pliku
``schema.sql`` (czysty DDL). Bootstrap wykonuje go idempotentnie
(wszystkie obiekty z ``IF NOT EXISTS``), więc kolejne starty nie
naruszają istniejących danych.
"""

import logging
from pathlib import Path

from app.db.engine import get_pool

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def apply_schema() -> None:
    """Wykonaj ``schema.sql`` na bazie (CREATE TABLE/INDEX IF NOT EXISTS)."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    pool = get_pool()
    async with pool.acquire() as conn:
        # asyncpg wykonuje wiele instrukcji oddzielonych ';' w jednym execute,
        # o ile nie przekazujemy parametrów (protokół prostych zapytań).
        await conn.execute(sql)
    logger.info("Relational schema applied from %s", SCHEMA_PATH.name)
