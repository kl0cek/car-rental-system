"""Schematy DTO dla zleceń serwisowych i historii serwisu.

Wykorzystywane przez panel technika do tworzenia/aktualizacji zleceń,
listingu z filtrami oraz dokumentowania wykonanych prac (notatki,
wymienione części, przebieg w momencie serwisu).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.service_order import ServiceOrderStatus, ServiceType


class ServiceOrderVehicleInfo(BaseModel):
    """Slim vehicle snapshot embedded in listing/detail responses.

    The technician panel needs brand/model/plate alongside every order — we
    embed it here so the frontend does not have to issue an extra request
    per row.
    """

    id: uuid.UUID
    brand: str
    model: str
    year: int
    license_plate: str
    mileage: int

    model_config = ConfigDict(from_attributes=True)


class ServiceOrderTechnicianInfo(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ServiceOrderCreate(BaseModel):
    vehicle_id: uuid.UUID
    type: ServiceType
    description: str = Field(min_length=1, max_length=2000)
    cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    scheduled_date: datetime
    # ``technician_id`` is optional: omitted means "assign to the caller" —
    # the service layer enforces this default. Admins may assign on behalf
    # of another technician by passing the id explicitly.
    technician_id: uuid.UUID | None = None


class ServiceOrderUpdate(BaseModel):
    type: ServiceType | None = None
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    scheduled_date: datetime | None = None
    technician_id: uuid.UUID | None = None


class ServiceOrderStatusUpdate(BaseModel):
    """Status transitions are a separate endpoint to keep validation rules tight."""

    status: ServiceOrderStatus
    # When transitioning to COMPLETED the technician may finalize the cost
    # estimate in the same call, avoiding a separate PUT round-trip.
    cost: Decimal | None = Field(default=None, ge=Decimal("0"))


class ServiceHistoryEntry(BaseModel):
    id: uuid.UUID
    notes: str
    parts_replaced: list[str]
    mileage_at_service: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceOrderResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    type: ServiceType
    status: ServiceOrderStatus
    description: str
    cost: Decimal | None
    scheduled_date: datetime
    completed_date: datetime | None
    technician_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceOrderDetailResponse(ServiceOrderResponse):
    """Detail view with eager-loaded vehicle / technician / history."""

    vehicle: ServiceOrderVehicleInfo
    technician: ServiceOrderTechnicianInfo
    history_entries: list[ServiceHistoryEntry] = Field(default_factory=list)


class ServiceOrderListItem(ServiceOrderResponse):
    """Row in the list view — embeds vehicle and technician without history."""

    vehicle: ServiceOrderVehicleInfo
    technician: ServiceOrderTechnicianInfo


class ServiceOrderListParams(BaseModel):
    """Query parameters for the listing endpoint."""

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: Literal["scheduled_date", "completed_date", "created_at", "cost"] = "scheduled_date"
    sort_order: Literal["asc", "desc"] = "desc"
    status: ServiceOrderStatus | None = None
    vehicle_id: uuid.UUID | None = None
    technician_id: uuid.UUID | None = None
    type: ServiceType | None = None
    scheduled_from: datetime | None = None
    scheduled_to: datetime | None = None

    @model_validator(mode="after")
    def _validate_scheduled_range(self) -> "ServiceOrderListParams":
        if (
            self.scheduled_from is not None
            and self.scheduled_to is not None
            and self.scheduled_from > self.scheduled_to
        ):
            raise ValueError("scheduled_from must be <= scheduled_to")
        return self


class PaginatedServiceOrderResponse(BaseModel):
    items: list[ServiceOrderListItem]
    total: int
    offset: int
    limit: int


class ServiceOrderStats(BaseModel):
    """Counters used by the order list view's summary cards."""

    scheduled: int = 0
    in_progress: int = 0
    completed: int = 0
    total: int = 0


class ServiceHistoryCreate(BaseModel):
    # ``vehicle_id`` is derived from the parent ``ServiceOrder`` at insert
    # time, so it is deliberately NOT part of the create payload.
    service_order_id: uuid.UUID
    notes: Annotated[str, Field(min_length=1, max_length=2000)]
    parts_replaced: list[str] = Field(default_factory=list)
    mileage_at_service: int = Field(ge=0)


class ServiceHistoryResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    service_order_id: uuid.UUID
    notes: str
    parts_replaced: list[str]
    mileage_at_service: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleServiceTimelineResponse(BaseModel):
    """Vehicle-centric timeline used by the maintenance history view."""

    vehicle_id: uuid.UUID
    orders: list[ServiceOrderListItem]
