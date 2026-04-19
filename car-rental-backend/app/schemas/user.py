import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.rental import ReservationStatus
from app.models.user import UserRole


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    phone: str | None
    avatar_url: str | None
    risk_score: Decimal
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "UserProfileUpdate":
        if all(v is None for v in (self.first_name, self.last_name, self.phone, self.email)):
            raise ValueError("At least one field must be provided")
        return self


class AvatarUploadResponse(BaseModel):
    avatar_url: str


UserRentalSortField = Literal["pickup_date", "return_date", "created_at"]


class UserRentalsListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: UserRentalSortField = Field(default="pickup_date")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    date_from: datetime | None = None
    date_to: datetime | None = None
    status: ReservationStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "UserRentalsListParams":
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must be before date_to")
        return self


class UserRentalVehicleInfo(BaseModel):
    id: uuid.UUID
    brand: str
    model: str
    year: int
    license_plate: str
    image_url: str | None

    model_config = {"from_attributes": True}


class UserRentalItem(BaseModel):
    id: uuid.UUID
    reservation_id: uuid.UUID
    vehicle: UserRentalVehicleInfo
    pickup_date: datetime
    return_date: datetime | None
    status: ReservationStatus
    total_price: Decimal
    final_price: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedUserRentalsResponse(BaseModel):
    items: list[UserRentalItem]
    total: int
    offset: int
    limit: int


AdminReservationSortField = Literal["created_at", "start_date", "end_date", "total_price"]


class AdminReservationListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: AdminReservationSortField = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    status: ReservationStatus | None = None
    user_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "AdminReservationListParams":
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must be before date_to")
        return self


class AdminReservationUserInfo(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class AdminReservationVehicleInfo(BaseModel):
    id: uuid.UUID
    brand: str
    model: str
    license_plate: str

    model_config = {"from_attributes": True}


class AdminReservationItem(BaseModel):
    id: uuid.UUID
    user: AdminReservationUserInfo
    vehicle: AdminReservationVehicleInfo
    start_date: datetime
    end_date: datetime
    status: ReservationStatus
    total_price: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAdminReservationsResponse(BaseModel):
    items: list[AdminReservationItem]
    total: int
    offset: int
    limit: int


AdminUserSortField = Literal[
    "created_at", "last_login_at", "risk_score", "email", "last_name"
]


class AdminUserListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: AdminUserSortField = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    min_risk_score: Decimal | None = Field(default=None, ge=0, le=100)
    max_risk_score: Decimal | None = Field(default=None, ge=0, le=100)
    active_since: datetime | None = None
    search: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_ranges(self) -> "AdminUserListParams":
        if (
            self.min_risk_score is not None
            and self.max_risk_score is not None
            and self.min_risk_score > self.max_risk_score
        ):
            raise ValueError("min_risk_score must be less than or equal to max_risk_score")
        return self


class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    phone: str | None
    avatar_url: str | None
    risk_score: Decimal
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAdminUsersResponse(BaseModel):
    items: list[AdminUserItem]
    total: int
    offset: int
    limit: int
