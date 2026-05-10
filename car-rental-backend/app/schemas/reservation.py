"""Schematy DTO dla rezerwacji.

Tworzenie rezerwacji przez klienta, zmiana statusu, zwracane
podsumowania (z danymi pojazdu i wyliczoną ceną).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.rental import Reservation, ReservationStatus
from app.models.vehicle_image import VehicleImage


class CreateReservationRequest(BaseModel):
    vehicle_id: uuid.UUID
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateReservationRequest":
        today = datetime.now(UTC).date()
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


def _primary_image_url(images: list[VehicleImage]) -> str | None:
    for img in images:
        if img.is_primary:
            return img.url
    if images:
        return min(images, key=lambda i: i.position).url
    return None


def build_reservation_response(reservation: Reservation) -> ReservationResponse:
    """Map a Reservation ORM row to its response DTO with primary-image URL.

    Centralised here so routers don't have to know the image-resolution rule.
    Caller is responsible for eager-loading ``reservation.vehicle.images``.
    """
    vehicle = reservation.vehicle
    return ReservationResponse(
        id=reservation.id,
        vehicle_id=reservation.vehicle_id,
        vehicle=ReservationVehicleInfo(
            id=vehicle.id,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year,
            license_plate=vehicle.license_plate,
            image_url=_primary_image_url(vehicle.images),
        ),
        start_date=reservation.start_date,
        end_date=reservation.end_date,
        status=reservation.status,
        total_price=reservation.total_price,
        created_at=reservation.created_at,
    )


@dataclass
class ReservationConfirmedEmailData:
    to_email: str
    first_name: str
    vehicle_name: str
    start_date: date
    end_date: date
    total_price: Decimal
