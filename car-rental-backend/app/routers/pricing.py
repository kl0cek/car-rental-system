"""Router wyceny wynajmu (`/pricing`).

Endpoint zwraca rozbicie ceny dla pary (pojazd, zakres dat) zgodnie ze
wzorem ``base_price * category_multiplier * risk_factor * days``.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser
from app.db.session import DbSession
from app.schemas.pricing import PriceBreakdownResponse
from app.services import pricing_service

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/quote", response_model=PriceBreakdownResponse)
async def quote_price(
    db: DbSession,
    current_user: CurrentUser,
    vehicle_id: uuid.UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> PriceBreakdownResponse:
    return await pricing_service.quote_price(
        db,
        current_user=current_user,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
    )
