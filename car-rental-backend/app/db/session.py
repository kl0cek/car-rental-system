"""Połączenie DB per request, transakcja i hooki po-commitowe (asyncpg).

``get_db`` to dependency FastAPI — pobiera połączenie z puli, otwiera
transakcję, commit'uje przy sukcesie i robi rollback przy każdym wyjątku.
``Db`` to cienka obwoluta na ``asyncpg.Connection`` (przekazuje
fetch/fetchrow/fetchval/execute) niosąca dodatkowo listę hooków
po-commitowych — odroczonych skutków ubocznych (np. usunięcie pliku),
które mają się wykonać dopiero gdy transakcja DB zakończy się sukcesem.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from typing import Annotated, Any

import asyncpg
from fastapi import Depends

from app.db.engine import get_pool

logger = logging.getLogger(__name__)

PostCommitHook = Callable[[], Awaitable[None]]


class Db:
    """Obwoluta połączenia asyncpg używana w warstwie repozytoriów.

    Metody odwzorowują API asyncpg 1:1 (placeholdery ``$1, $2, ...``),
    a ``post_commit_hooks`` przechowuje odroczone skutki uboczne.
    """

    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn
        self.post_commit_hooks: list[PostCommitHook] = []

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        return await self.conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        return await self.conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        return await self.conn.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        return await self.conn.execute(query, *args)

    async def executemany(self, query: str, args: Sequence[Sequence[Any]]) -> None:
        await self.conn.executemany(query, args)


def schedule_post_commit(db: Db, hook: PostCommitHook) -> None:
    """Uruchom ``hook`` dopiero po udanym commicie transakcji żądania.

    Mutacje na systemie plików (np. skasowanie poprzedniego zdjęcia) nie mogą
    nastąpić, dopóki transakcja DB jest otwarta — późniejszy wyjątek wycofałby
    bazę, ale plik byłby już usunięty. Tym mechanizmem je odraczamy.
    """
    db.post_commit_hooks.append(hook)


async def _run_post_commit_hooks(db: Db) -> None:
    hooks = db.post_commit_hooks
    db.post_commit_hooks = []
    for hook in hooks:
        try:
            await hook()
        except asyncio.CancelledError:
            raise
        except Exception:
            # Best-effort cleanup; never fail the response because cleanup failed.
            logger.exception("post-commit hook failed")


async def get_db() -> AsyncGenerator[Db]:
    # Jedno połączenie per request: commit przy sukcesie, rollback przy wyjątku.
    # Hooki post-commit odpalają się TYLKO gdy commit się udał.
    pool = get_pool()
    async with pool.acquire() as conn:
        db = Db(conn)
        tx = conn.transaction()
        await tx.start()
        try:
            yield db
        except Exception:
            await tx.rollback()
            raise
        else:
            await tx.commit()
            await _run_post_commit_hooks(db)


DbSession = Annotated[Db, Depends(get_db)]
