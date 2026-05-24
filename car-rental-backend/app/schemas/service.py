"""Schematy DTO dla zleceń serwisowych i historii serwisu.

Wykorzystywane przez panel technika do tworzenia/aktualizacji zleceń
oraz dokumentowania wykonanych prac (notatki, wymienione części,
przebieg w momencie serwisu).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.service_order import ServiceOrderStatus, ServiceType


class ServiceOrderCreate(BaseModel):
    vehicle_id: uuid.UUID
    type: ServiceType
    description: str = Field(min_length=1, max_length=2000)
    cost: Decimal | None = None
    scheduled_date: datetime
    technician_id: uuid.UUID


class ServiceOrderUpdate(BaseModel):
    type: ServiceType | None = None
    status: ServiceOrderStatus | None = None
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    cost: Decimal | None = None
    scheduled_date: datetime | None = None
    completed_date: datetime | None = None
    technician_id: uuid.UUID | None = None


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


class ServiceHistoryCreate(BaseModel):
    # ``vehicle_id`` is derived from the parent ``ServiceOrder`` at insert
    # time, so it is deliberately NOT part of the create payload.
    service_order_id: uuid.UUID
    notes: str = Field(min_length=1, max_length=2000)
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
