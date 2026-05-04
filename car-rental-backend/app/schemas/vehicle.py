"""Schematy DTO dla katalogu pojazdów i panelu admina pojazdów.

Walidacja parametrów filtrowania (zakres dat, kategoria, typ silnika),
schemat tworzenia/aktualizacji oraz odpowiedzi z wyliczoną
ceną dzienną.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.category import CategoryName
from app.models.vehicle import EngineType, VehicleStatus

VIN_LENGTH = 17
LICENSE_PLATE_MAX = 20
BRAND_MAX = 100
MODEL_MAX = 100
COLOR_MAX = 50
MIN_YEAR = 1900

SortableField = Literal[
    "brand", "model", "year", "daily_base_price", "created_at", "mileage", "horsepower"
]


class VehicleListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: SortableField = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")

    # Filters
    category: CategoryName | None = None
    engine_type: EngineType | None = None
    min_price: Decimal | None = Field(default=None, ge=0, le=99999999)
    max_price: Decimal | None = Field(default=None, ge=0, le=99999999)
    min_year: int | None = Field(default=None, ge=1900)
    max_year: int | None = Field(default=None, le=2100)
    min_seats: int | None = Field(default=None, ge=1)
    status: VehicleStatus | None = None
    available_from: date | None = None
    available_to: date | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> "VehicleListParams":
        if self.available_from is not None and self.available_to is not None:
            if self.available_from > self.available_to:
                raise ValueError("available_from must be before available_to")
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price must be less than or equal to max_price")
        if self.min_year is not None and self.max_year is not None:
            if self.min_year > self.max_year:
                raise ValueError("min_year must be less than or equal to max_year")
        return self


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: CategoryName
    description: str | None
    price_multiplier: Decimal

    model_config = {"from_attributes": True}


class VehicleListItem(BaseModel):
    id: uuid.UUID
    brand: str
    model: str
    year: int
    engine_type: EngineType
    horsepower: int
    seats: int
    trunk_capacity: int
    daily_base_price: Decimal
    color: str
    mileage: int
    image_url: str | None
    status: VehicleStatus
    category: CategoryResponse

    model_config = {"from_attributes": True}


class PaginatedVehicleResponse(BaseModel):
    items: list[VehicleListItem]
    total: int
    offset: int
    limit: int


class BookedDateRange(BaseModel):
    start_date: datetime
    end_date: datetime


class VehicleDetailResponse(BaseModel):
    id: uuid.UUID
    brand: str
    model: str
    year: int
    engine_type: EngineType
    horsepower: int
    seats: int
    trunk_capacity: int
    daily_base_price: Decimal
    color: str
    mileage: int
    image_url: str | None
    status: VehicleStatus
    is_active: bool
    category: CategoryResponse
    average_rating: float | None
    review_count: int
    booked_dates: list[BookedDateRange]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityRequest(BaseModel):
    start_date: date
    end_date: date


class AvailabilityResponse(BaseModel):
    vehicle_id: uuid.UUID
    available: bool
    start_date: date
    end_date: date
    conflicting_rentals: int = 0


def _current_year() -> int:
    return datetime.now(timezone.utc).year


class VehicleCreate(BaseModel):
    """Schema for creating a vehicle. Image is handled separately via multipart upload."""

    brand: str = Field(min_length=1, max_length=BRAND_MAX)
    model: str = Field(min_length=1, max_length=MODEL_MAX)
    year: int = Field(ge=MIN_YEAR)
    license_plate: str = Field(min_length=1, max_length=LICENSE_PLATE_MAX)
    vin: str = Field(min_length=VIN_LENGTH, max_length=VIN_LENGTH)
    engine_type: EngineType
    horsepower: int = Field(gt=0)
    seats: int = Field(gt=0)
    trunk_capacity: int = Field(ge=0)
    daily_base_price: Decimal = Field(gt=0, le=Decimal("99999999.99"))
    color: str = Field(min_length=1, max_length=COLOR_MAX)
    category_id: uuid.UUID
    mileage: int = Field(default=0, ge=0)
    status: VehicleStatus = VehicleStatus.AVAILABLE

    @field_validator("year")
    @classmethod
    def _validate_year(cls, value: int) -> int:
        max_year = _current_year() + 1
        if value > max_year:
            raise ValueError(f"year must be at most {max_year}")
        return value

    @field_validator("vin")
    @classmethod
    def _normalize_vin(cls, value: str) -> str:
        v = value.strip().upper()
        if len(v) != VIN_LENGTH:
            raise ValueError("VIN must be exactly 17 characters")
        return v

    @field_validator("license_plate")
    @classmethod
    def _normalize_license_plate(cls, value: str) -> str:
        return value.strip().upper()


class VehicleUpdate(BaseModel):
    """Partial update — all fields optional. Image handled separately."""

    brand: str | None = Field(default=None, min_length=1, max_length=BRAND_MAX)
    model: str | None = Field(default=None, min_length=1, max_length=MODEL_MAX)
    year: int | None = Field(default=None, ge=MIN_YEAR)
    license_plate: str | None = Field(default=None, min_length=1, max_length=LICENSE_PLATE_MAX)
    vin: str | None = Field(default=None, min_length=VIN_LENGTH, max_length=VIN_LENGTH)
    engine_type: EngineType | None = None
    horsepower: int | None = Field(default=None, gt=0)
    seats: int | None = Field(default=None, gt=0)
    trunk_capacity: int | None = Field(default=None, ge=0)
    daily_base_price: Decimal | None = Field(default=None, gt=0, le=Decimal("99999999.99"))
    color: str | None = Field(default=None, min_length=1, max_length=COLOR_MAX)
    category_id: uuid.UUID | None = None
    mileage: int | None = Field(default=None, ge=0)
    status: VehicleStatus | None = None

    @field_validator("year")
    @classmethod
    def _validate_year(cls, value: int | None) -> int | None:
        if value is None:
            return value
        max_year = _current_year() + 1
        if value > max_year:
            raise ValueError(f"year must be at most {max_year}")
        return value

    @field_validator("vin")
    @classmethod
    def _normalize_vin(cls, value: str | None) -> str | None:
        if value is None:
            return value
        v = value.strip().upper()
        if len(v) != VIN_LENGTH:
            raise ValueError("VIN must be exactly 17 characters")
        return v

    @field_validator("license_plate")
    @classmethod
    def _normalize_license_plate(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().upper()
