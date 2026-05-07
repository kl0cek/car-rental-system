"""Schematy DTO dla panelu klienta widzianego przez pracownika.

Obejmują widok szczegółów klienta z agregacją danych: profil, statystyki
wynajmów, lista incydentów, lista notatek, historia rezerwacji.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentType
from app.models.user import UserRole


class IncidentAuthorInfo(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class IncidentResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    rental_id: uuid.UUID | None
    type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    reported_by: IncidentAuthorInfo
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    rental_id: uuid.UUID | None = None
    type: IncidentType
    severity: IncidentSeverity
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)


class CustomerNoteAuthorInfo(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}


class CustomerNoteResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    body: str
    author: CustomerNoteAuthorInfo
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CustomerNoteUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CustomerRentalSummary(BaseModel):
    """Compact rental view shown inside the customer detail page."""

    id: uuid.UUID
    vehicle_name: str
    license_plate: str
    pickup_date: datetime
    return_date: datetime | None
    status: str
    total_price: Decimal
    final_price: Decimal | None


class CustomerStats(BaseModel):
    total_rentals: int
    completed_rentals: int
    cancelled_rentals: int
    total_spent: Decimal
    incident_count: int


class CustomerProfile(BaseModel):
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


class CustomerDetailResponse(BaseModel):
    profile: CustomerProfile
    stats: CustomerStats
    rentals: list[CustomerRentalSummary]
    incidents: list[IncidentResponse]
    notes: list[CustomerNoteResponse]
