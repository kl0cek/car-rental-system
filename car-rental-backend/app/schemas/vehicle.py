import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.category import CategoryName
from app.models.vehicle import EngineType, VehicleStatus

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
