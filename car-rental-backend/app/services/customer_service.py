"""Serwis panelu klienta dostępnego dla pracownika.

Agreguje profil klienta, statystyki wynajmów (z ``rentals`` + breakdown),
listę incydentów i notatek wewnętrznych. CRUD dla incydentów i notatek
żyje tutaj — to logika biznesowa nie wymagająca odrębnego serwisu.
"""

import uuid
from decimal import Decimal

from fastapi import HTTPException, status

from app.db.redis import get_redis
from app.db.session import Db
from app.models.customer_note import CustomerNote
from app.models.incident import Incident
from app.models.rental import ReservationStatus
from app.models.user import User, UserRole
from app.repositories import (
    customer_note_repository,
    incident_repository,
    rental_repository,
    user_repository,
)
from app.schemas.customer import (
    CustomerDetailResponse,
    CustomerNoteCreate,
    CustomerNoteResponse,
    CustomerNoteUpdate,
    CustomerProfile,
    CustomerRentalSummary,
    CustomerStats,
    IncidentCreate,
    IncidentResponse,
)
from app.services import risk_scoring


async def _ensure_customer(db: Db, customer_id: uuid.UUID) -> User:
    user = await user_repository.get_by_id(db, customer_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if user.role != UserRole.CUSTOMER:
        # Endpoint is only meaningful for customers — bouncing on staff prevents
        # leaking employee data through this view by passing a wrong id.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target user is not a customer",
        )
    return user


async def _load_rental_history(db: Db, customer_id: uuid.UUID) -> list[CustomerRentalSummary]:
    # Reużywamy repozytorium wynajmów (dociąga rezerwację + pojazd + breakdown).
    # Limit 10000 jest praktyczną górną granicą historii pojedynczego klienta.
    rentals, _ = await rental_repository.get_list_by_user(
        db, customer_id, offset=0, limit=10000, sort_by="pickup_date", sort_order="desc"
    )

    summaries: list[CustomerRentalSummary] = []
    for rental in rentals:
        reservation = rental.reservation
        if reservation is None or reservation.vehicle is None:
            continue
        vehicle = reservation.vehicle
        summaries.append(
            CustomerRentalSummary(
                id=rental.id,
                vehicle_name=f"{vehicle.brand} {vehicle.model} ({vehicle.year})",
                license_plate=vehicle.license_plate,
                pickup_date=rental.pickup_date,
                return_date=rental.return_date,
                status=str(reservation.status.value),
                total_price=reservation.total_price,
                final_price=(
                    rental.price_breakdown.final_price if rental.price_breakdown else None
                ),
            )
        )
    return summaries


async def _compute_stats(db: Db, customer_id: uuid.UUID) -> CustomerStats:
    # Wszystkie liczniki i suma jednym zapytaniem (FILTER), by czas odpowiedzi był
    # ograniczony nawet dla klientów z tysiącami rezerwacji.
    row = await db.fetchrow(
        "SELECT count(*) AS total, "
        "coalesce(sum(total_price), 0) AS spent, "
        "count(*) FILTER (WHERE status = $2) AS completed, "
        "count(*) FILTER (WHERE status = $3) AS cancelled "
        "FROM reservations WHERE user_id = $1",
        customer_id,
        ReservationStatus.COMPLETED.value,
        ReservationStatus.CANCELLED.value,
    )
    assert row is not None

    incident_count = await incident_repository.count_for_customer(db, customer_id)

    return CustomerStats(
        total_rentals=row["total"] or 0,
        completed_rentals=row["completed"] or 0,
        cancelled_rentals=row["cancelled"] or 0,
        total_spent=Decimal(row["spent"] or 0).quantize(Decimal("0.01")),
        incident_count=incident_count,
    )


async def get_customer_detail(db: Db, customer_id: uuid.UUID) -> CustomerDetailResponse:
    user = await _ensure_customer(db, customer_id)

    rentals = await _load_rental_history(db, customer_id)
    stats = await _compute_stats(db, customer_id)
    incidents = await incident_repository.list_for_customer(db, customer_id)
    notes = await customer_note_repository.list_for_customer(db, customer_id)

    return CustomerDetailResponse(
        profile=CustomerProfile.model_validate(user),
        stats=stats,
        rentals=rentals,
        incidents=[IncidentResponse.model_validate(i) for i in incidents],
        notes=[CustomerNoteResponse.model_validate(n) for n in notes],
    )


async def create_incident(
    db: Db,
    customer_id: uuid.UUID,
    reporter: User,
    body: IncidentCreate,
) -> IncidentResponse:
    await _ensure_customer(db, customer_id)

    if body.rental_id is not None:
        # Confirm the rental belongs to this customer — otherwise we'd silently
        # let staff associate an incident with anybody's rental.
        owner = await db.fetchval(
            "SELECT r.id FROM rentals r JOIN reservations res ON res.id = r.reservation_id "
            "WHERE r.id = $1 AND res.user_id = $2",
            body.rental_id,
            customer_id,
        )
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="rental_id does not belong to this customer",
            )

    incident = Incident(
        customer_id=customer_id,
        rental_id=body.rental_id,
        reported_by_id=reporter.id,
        type=body.type,
        severity=body.severity,
        title=body.title,
        description=body.description,
        cost=body.cost,
    )
    saved = await incident_repository.create(db, incident)
    # Event-driven: a new incident affects the customer's risk profile.
    await risk_scoring.recompute_and_persist(db, customer_id, get_redis())
    return IncidentResponse.model_validate(saved)


async def delete_incident(
    db: Db,
    customer_id: uuid.UUID,
    incident_id: uuid.UUID,
) -> None:
    incident = await incident_repository.get_by_id(db, incident_id)
    if incident is None or incident.customer_id != customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await incident_repository.delete(db, incident)
    # Event-driven: removing an incident also affects the customer's risk profile.
    await risk_scoring.recompute_and_persist(db, customer_id, get_redis())


async def create_note(
    db: Db,
    customer_id: uuid.UUID,
    author: User,
    body: CustomerNoteCreate,
) -> CustomerNoteResponse:
    await _ensure_customer(db, customer_id)
    note = CustomerNote(customer_id=customer_id, author_id=author.id, body=body.body)
    saved = await customer_note_repository.create(db, note)
    return CustomerNoteResponse.model_validate(saved)


async def update_note(
    db: Db,
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
    body: CustomerNoteUpdate,
) -> CustomerNoteResponse:
    note = await customer_note_repository.get_by_id(db, note_id)
    if note is None or note.customer_id != customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    note.body = body.body
    saved = await customer_note_repository.update(db, note)
    return CustomerNoteResponse.model_validate(saved)


async def delete_note(
    db: Db,
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
) -> None:
    note = await customer_note_repository.get_by_id(db, note_id)
    if note is None or note.customer_id != customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    await customer_note_repository.delete(db, note)
