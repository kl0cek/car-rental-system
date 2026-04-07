import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PickupRequest(BaseModel):
    mileage_start: int = Field(ge=0)
    fuel_level_start: Decimal = Field(ge=0, le=100)
    photo_urls: list[str] = Field(default_factory=list)
    client_signature_url: str | None = None


class ReturnRequest(BaseModel):
    mileage_end: int = Field(ge=0)
    fuel_level_end: Decimal = Field(ge=0, le=100)
    damage_notes: str | None = None
    damage_photo_urls: list[str] = Field(default_factory=list)
    extra_charges: Decimal = Field(default=Decimal("0"), ge=0)


class RentalPriceBreakdownResponse(BaseModel):
    base_price: Decimal
    fuel_surcharge: Decimal
    risk_multiplier: Decimal
    final_price: Decimal
    calculated_at: datetime

    model_config = {"from_attributes": True}


class RentalResponse(BaseModel):
    id: uuid.UUID
    reservation_id: uuid.UUID
    pickup_date: datetime
    return_date: datetime | None
    mileage_start: int
    mileage_end: int | None
    fuel_level_start: Decimal
    fuel_level_end: Decimal | None
    damage_notes: str | None
    employee_id: uuid.UUID
    price_breakdown: RentalPriceBreakdownResponse | None
    created_at: datetime

    model_config = {"from_attributes": True}
