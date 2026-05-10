"""Sesja DB per request i mechanizm hooków po-commitowych.

`get_db` jest dependency FastAPI — otwiera transakcję, commit'uje przy
sukcesie, robi rollback przy wyjątku. `schedule_post_commit` pozwala
odłożyć skutki uboczne (np. usunięcie pliku) do momentu, w którym
transakcja DB zakończyła się sukcesem.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)

PostCommitHook = Callable[[], Awaitable[None]]
_HOOKS_KEY = "post_commit_hooks"


def schedule_post_commit(session: AsyncSession, hook: PostCommitHook) -> None:
    """Run ``hook`` only after the request transaction commits successfully.

    Filesystem mutations (e.g. unlinking a previous image) must not happen
    while the SQLAlchemy transaction is still open: a later exception would
    roll back the DB but leave the filesystem changed. Defer them with this.
    """
    hooks: list[PostCommitHook] = session.info.setdefault(_HOOKS_KEY, [])
    hooks.append(hook)


async def _run_post_commit_hooks(session: AsyncSession) -> None:
    hooks: list[PostCommitHook] = session.info.pop(_HOOKS_KEY, [])
    for hook in hooks:
        try:
            await hook()
        except asyncio.CancelledError:
            raise
        except Exception:
            # Best-effort cleanup; never fail the response because cleanup failed.
            # Logged so orphaned-resource accumulation is observable.
            logger.exception("post-commit hook failed")


async def get_db() -> AsyncGenerator[AsyncSession]:
    # Jedna sesja per request: commit przy sukcesie, rollback przy każdym wyjątku.
    # Hooki post-commit odpalają się TYLKO gdy commit się udał — błąd routera
    # po commicie też nie wyzwoli hooków, bo sterowanie wraca przez wyjątek.
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        else:
            await _run_post_commit_hooks(session)


DbSession = Annotated[AsyncSession, Depends(get_db)]
