import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

SORTABLE_COLUMNS = {
    "created_at": User.created_at,
    "last_login_at": User.last_login_at,
    "risk_score": User.risk_score,
    "email": User.email,
    "last_name": User.last_name,
}


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User) -> User:
    await db.flush()
    await db.refresh(user)
    return user


def _apply_admin_filters(
    stmt: Select[tuple[User]],
    *,
    role: UserRole | None,
    is_active: bool | None,
    is_verified: bool | None,
    min_risk_score: Decimal | None,
    max_risk_score: Decimal | None,
    active_since: datetime | None,
    search: str | None,
) -> Select[tuple[User]]:
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    if is_verified is not None:
        stmt = stmt.where(User.is_verified.is_(is_verified))
    if min_risk_score is not None:
        stmt = stmt.where(User.risk_score >= min_risk_score)
    if max_risk_score is not None:
        stmt = stmt.where(User.risk_score <= max_risk_score)
    if active_since is not None:
        stmt = stmt.where(User.last_login_at >= active_since)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(pattern, escape="\\"),
                User.first_name.ilike(pattern, escape="\\"),
                User.last_name.ilike(pattern, escape="\\"),
            )
        )
    return stmt


async def get_admin_list(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    role: UserRole | None = None,
    is_active: bool | None = None,
    is_verified: bool | None = None,
    min_risk_score: Decimal | None = None,
    max_risk_score: Decimal | None = None,
    active_since: datetime | None = None,
    search: str | None = None,
) -> tuple[list[User], int]:
    base = select(User)
    base = _apply_admin_filters(
        base,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        active_since=active_since,
        search=search,
    )

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_col = SORTABLE_COLUMNS.get(sort_by, User.created_at)
    order = sort_col.asc() if sort_order == "asc" else sort_col.desc()
    # last_login_at is nullable — ensure NULLs are last when descending, first when ascending
    if sort_by == "last_login_at":
        order = order.nulls_last() if sort_order == "desc" else order.nulls_first()

    stmt = base.order_by(order).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().unique()), total


async def update_last_login(db: AsyncSession, user: User, when: datetime) -> None:
    user.last_login_at = when
    await db.flush()
