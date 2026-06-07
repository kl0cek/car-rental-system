"""Serwis wyliczania ceny wynajmu.

Wzór: ``base_price * risk_factor * category_multiplier * days``.

* ``base_price`` — dzienna cena bazowa pojazdu (``Vehicle.daily_base_price``).
* ``category_multiplier`` — mnożnik kategorii (``Category.price_multiplier``).
* ``risk_factor`` — mnożnik wyliczany z ``User.risk_score`` (zob.
  :func:`app.services.rental_service.compute_risk_multiplier`).
* ``days`` — liczba dni między ``start_date`` i ``end_date`` (min. 1).

Endpoint zwraca również ``base_subtotal`` (bez korekty ryzyka) oraz
``risk_adjustment`` — różnicę narzucaną/odejmowaną przez ryzyko —
żeby UI mógł pokazać czytelny breakdown.
"""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status

from app.db.session import Db
from app.models.user import User
from app.repositories import vehicle_repository
from app.schemas.pricing import PriceBreakdownResponse
from app.services.rental_service import compute_risk_multiplier

MONEY_QUANT = Decimal("0.01")


def _days_between(start: date, end: date) -> int:
    return max(1, (end - start).days)


async def quote_price(
    db: Db,
    *,
    current_user: User,
    vehicle_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> PriceBreakdownResponse:
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be after start_date",
        )

    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    days = _days_between(start_date, end_date)
    daily_base = vehicle.daily_base_price
    category_mult = vehicle.category.price_multiplier
    risk_mult = compute_risk_multiplier(current_user.risk_score)

    base_subtotal = (daily_base * category_mult * Decimal(days)).quantize(MONEY_QUANT)
    total = (base_subtotal * risk_mult).quantize(MONEY_QUANT)
    risk_adjustment = (total - base_subtotal).quantize(MONEY_QUANT)
    price_per_day = (total / Decimal(days)).quantize(MONEY_QUANT)

    return PriceBreakdownResponse(
        vehicle_id=vehicle.id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        daily_base_price=daily_base.quantize(MONEY_QUANT),
        category_multiplier=category_mult,
        risk_multiplier=risk_mult,
        risk_adjustment=risk_adjustment,
        base_subtotal=base_subtotal,
        price_per_day=price_per_day,
        total=total,
    )
