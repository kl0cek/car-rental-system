"""Repozytorium użytkowników — czysty SQL na tabeli ``users`` (asyncpg).

Warstwa repozytorium izoluje serwisy od szczegółów persystencji: zwraca
obiekty domenowe (``User``) i przyjmuje proste argumenty. Zapytania są
parametryzowane ($1, $2, ...) — bez sklejania wartości w string.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from app.db.session import Db
from app.models.user import User, UserRole

# Whitelist kolumn dozwolonych w ORDER BY (ochrona przed SQL injection w sort_by).
SORTABLE_COLUMNS = {
    "created_at": "created_at",
    "last_login_at": "last_login_at",
    "risk_score": "risk_score",
    "email": "email",
    "last_name": "last_name",
}

_INSERT_COLS = (
    "id, email, hashed_password, first_name, last_name, role, is_active, "
    "is_verified, phone, avatar_url, risk_score, last_login_at"
)


async def get_by_id(db: Db, user_id: uuid.UUID) -> User | None:
    row = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    return User.from_row(row) if row else None


async def get_by_email(db: Db, email: str) -> User | None:
    row = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)
    return User.from_row(row) if row else None


async def create(db: Db, user: User) -> User:
    row = await db.fetchrow(
        f"INSERT INTO users ({_INSERT_COLS}) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) RETURNING *",
        user.id,
        user.email,
        user.hashed_password,
        user.first_name,
        user.last_name,
        user.role.value,
        user.is_active,
        user.is_verified,
        user.phone,
        user.avatar_url,
        user.risk_score,
        user.last_login_at,
    )
    assert row is not None
    return User.from_row(row)


async def update(db: Db, user: User) -> User:
    row = await db.fetchrow(
        "UPDATE users SET email = $2, hashed_password = $3, first_name = $4, last_name = $5, "
        "role = $6, is_active = $7, is_verified = $8, phone = $9, avatar_url = $10, "
        "risk_score = $11, last_login_at = $12, updated_at = now() WHERE id = $1 RETURNING *",
        user.id,
        user.email,
        user.hashed_password,
        user.first_name,
        user.last_name,
        user.role.value,
        user.is_active,
        user.is_verified,
        user.phone,
        user.avatar_url,
        user.risk_score,
        user.last_login_at,
    )
    assert row is not None
    return User.from_row(row)


async def get_admin_list(
    db: Db,
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
    conditions: list[str] = []
    args: list[object] = []

    def add(template: str, value: object) -> None:
        args.append(value)
        conditions.append(template.format(n=len(args)))

    if role is not None:
        add("role = ${n}", role.value)
    if is_active is not None:
        add("is_active = ${n}", is_active)
    if is_verified is not None:
        add("is_verified = ${n}", is_verified)
    if min_risk_score is not None:
        add("risk_score >= ${n}", min_risk_score)
    if max_risk_score is not None:
        add("risk_score <= ${n}", max_risk_score)
    if active_since is not None:
        add("last_login_at >= ${n}", active_since)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        args.append(f"%{escaped}%")
        n = len(args)
        conditions.append(f"(email ILIKE ${n} OR first_name ILIKE ${n} OR last_name ILIKE ${n})")

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total = await db.fetchval(f"SELECT count(*) FROM users{where}", *args)

    sort_col = SORTABLE_COLUMNS.get(sort_by, "created_at")
    direction = "ASC" if sort_order == "asc" else "DESC"
    nulls = ""
    if sort_by == "last_login_at":
        nulls = " NULLS LAST" if sort_order == "desc" else " NULLS FIRST"

    rows = await db.fetch(
        f"SELECT * FROM users{where} ORDER BY {sort_col} {direction}{nulls} "
        f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args,
        limit,
        offset,
    )
    return [User.from_row(r) for r in rows], int(total or 0)


async def update_last_login(db: Db, user: User, when: datetime) -> None:
    await db.execute(
        "UPDATE users SET last_login_at = $2, updated_at = now() WHERE id = $1",
        user.id,
        when,
    )
    user.last_login_at = when
