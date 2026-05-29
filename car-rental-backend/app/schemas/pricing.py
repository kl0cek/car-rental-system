"""Schematy DTO dla rozbicia ceny wynajmu.

Wyliczenie po stronie API zwraca jednoznaczny podział na czynniki ceny
(`base * risk * category * dni`) — żeby UI mógł pokazać klientowi z
czego wynika końcowa kwota, zanim potwierdzi rezerwację.
"""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PriceQuoteRequest(BaseModel):
    vehicle_id: uuid.UUID
    start_date: date
    end_date: date


class PriceBreakdownResponse(BaseModel):
    vehicle_id: uuid.UUID
    start_date: date
    end_date: date
    days: int
    daily_base_price: Decimal
    category_multiplier: Decimal
    risk_multiplier: Decimal
    risk_adjustment: Decimal
    base_subtotal: Decimal
    price_per_day: Decimal
    total: Decimal
