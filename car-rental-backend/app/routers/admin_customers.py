"""Router panelu klienta widzianego przez pracownika (`/admin/customers`).

Pracownik / admin może obejrzeć szczegóły klienta (profil, wynajmy,
incydenty, notatki) oraz dodawać/usuwać incydenty i CRUD-ować notatki
wewnętrzne. Wymaga roli EMPLOYEE lub ADMIN.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import require_roles
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.schemas.customer import (
    CustomerDetailResponse,
    CustomerNoteCreate,
    CustomerNoteResponse,
    CustomerNoteUpdate,
    IncidentCreate,
    IncidentResponse,
)
from app.services import customer_service

router = APIRouter(prefix="/admin/customers", tags=["admin", "customers"])

StaffUser = Annotated[
    User,
    Depends(require_roles(UserRole.EMPLOYEE, UserRole.TECHNICIAN, UserRole.ADMIN)),
]


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer_detail(
    customer_id: uuid.UUID,
    db: DbSession,
    _: StaffUser,
) -> CustomerDetailResponse:
    return await customer_service.get_customer_detail(db, customer_id)


@router.post(
    "/{customer_id}/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_incident(
    customer_id: uuid.UUID,
    body: IncidentCreate,
    db: DbSession,
    current_user: StaffUser,
) -> IncidentResponse:
    return await customer_service.create_incident(db, customer_id, current_user, body)


@router.delete(
    "/{customer_id}/incidents/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_customer_incident(
    customer_id: uuid.UUID,
    incident_id: uuid.UUID,
    db: DbSession,
    _: StaffUser,
) -> Response:
    await customer_service.delete_incident(db, customer_id, incident_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{customer_id}/notes",
    response_model=CustomerNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_note(
    customer_id: uuid.UUID,
    body: CustomerNoteCreate,
    db: DbSession,
    current_user: StaffUser,
) -> CustomerNoteResponse:
    return await customer_service.create_note(db, customer_id, current_user, body)


@router.put(
    "/{customer_id}/notes/{note_id}",
    response_model=CustomerNoteResponse,
)
async def update_customer_note(
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
    body: CustomerNoteUpdate,
    db: DbSession,
    _: StaffUser,
) -> CustomerNoteResponse:
    return await customer_service.update_note(db, customer_id, note_id, body)


@router.delete(
    "/{customer_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_customer_note(
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
    db: DbSession,
    _: StaffUser,
) -> Response:
    await customer_service.delete_note(db, customer_id, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


