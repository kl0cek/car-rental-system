import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.rental import ReservationStatus


class CreateReservationRequest(BaseModel):
    vehicle_id: uuid.UUID
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateReservationRequest":
        today = date.today()
        if self.start_date < today:
            raise ValueError("start_date must not be in the past")
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class ReservationVehicleInfo(BaseModel):
    id: uuid.UUID
    brand: str
    model: str
    year: int
    license_plate: str
    image_url: str | None

    model_config = {"from_attributes": True}


class ReservationResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    vehicle: ReservationVehicleInfo
    start_date: datetime
    end_date: datetime
    status: ReservationStatus
    total_price: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ReservationListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    status: ReservationStatus | None = None


class PaginatedReservationResponse(BaseModel):
    items: list[ReservationResponse]
    total: int
    offset: int
    limit: int
