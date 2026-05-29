"""Serwis zleceń serwisowych.

Reguły biznesowe trzymane w jednym miejscu, żeby router pozostał cienki:

* tworzenie zlecenia **automatycznie** przełącza pojazd w status
  ``MAINTENANCE`` (jeżeli był ``AVAILABLE``) — pojazdy aktywnie wynajęte
  (``RENTED``) nie są dotykane: technik dostaje samochód do garażu
  dopiero po zwrocie, ale zlecenie planowo i tak da się utworzyć,
* tworzenia zlecenia nie da się zaplanować na pojazd z aktywną rezerwacją
  (``PENDING``/``CONFIRMED``/``ACTIVE``) — zlecenie blokowałoby wydanie,
  więc operator musi najpierw anulować/zwrócić rezerwację,
* zamknięcie zlecenia (status ``COMPLETED``) zwraca pojazd do
  ``AVAILABLE``, o ile nie istnieje żadne inne wciąż otwarte zlecenie
  serwisowe.

Transakcje są chronione blokadami ``SELECT ... FOR UPDATE`` na wierszu
pojazdu — dwa równoczesne zlecenia nie nadpiszą sobie nawzajem statusu
pojazdu.
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_order import ServiceOrder, ServiceOrderStatus
from app.models.user import User, UserRole
from app.models.vehicle import VehicleStatus
from app.repositories import service_repository, vehicle_repository
from app.schemas.service import (
    ServiceHistoryCreate,
    ServiceOrderCreate,
    ServiceOrderListParams,
    ServiceOrderStats,
    ServiceOrderStatusUpdate,
    ServiceOrderUpdate,
)

# Status transitions allowed in this state machine. Anything outside this
# whitelist is rejected with 422 — keeps the technician panel honest and
# protects vehicle-status side effects from being triggered out of order.
_ALLOWED_TRANSITIONS: dict[ServiceOrderStatus, set[ServiceOrderStatus]] = {
    ServiceOrderStatus.SCHEDULED: {ServiceOrderStatus.IN_PROGRESS, ServiceOrderStatus.COMPLETED},
    ServiceOrderStatus.IN_PROGRESS: {ServiceOrderStatus.COMPLETED},
    ServiceOrderStatus.COMPLETED: set(),
}


def _ensure_technician_role(user: User) -> None:
    if user.role != UserRole.TECHNICIAN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assigned user must have the technician role",
        )


def _ensure_can_manage(current_user: User, order: ServiceOrder) -> None:
    """Admins may manage any order; technicians only their own."""
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.TECHNICIAN and order.technician_id == current_user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only manage your own service orders",
    )


async def _resolve_technician(
    db: AsyncSession,
    current_user: User,
    requested_id: uuid.UUID | None,
) -> uuid.UUID:
    """Default to the caller when no id is given, otherwise validate role."""
    # Avoid the circular import — user_repository imports nothing from us,
    # but keeping it local makes the dependency direction explicit.
    from app.repositories import user_repository

    if requested_id is None or requested_id == current_user.id:
        if current_user.role != UserRole.TECHNICIAN:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only technicians can be assigned to a service order",
            )
        return current_user.id

    # Admin re-assigning to another tech: load the target and verify.
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign service orders to other technicians",
        )
    target = await user_repository.get_by_id(db, requested_id)
    if target is None or not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found",
        )
    _ensure_technician_role(target)
    return target.id


async def _vehicle_has_blocking_workload(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> bool:
    """True if any reservation/active rental would conflict with maintenance."""
    return await vehicle_repository.has_blocking_reservations(db, vehicle_id)


async def create_order(
    db: AsyncSession,
    current_user: User,
    body: ServiceOrderCreate,
) -> ServiceOrder:
    # Pull and lock the vehicle: blocks racing reservations / other service
    # orders from flipping its status while we evaluate the transition.
    vehicle = await vehicle_repository.get_by_id_for_update(db, body.vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    if vehicle.status == VehicleStatus.OUT_OF_SERVICE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot schedule a service order for an out-of-service vehicle",
        )

    # Don't accept a service order when the car is booked out — operator
    # has to cancel the reservation first. We allow scheduling on a
    # currently RENTED car so the technician can plan ahead for the
    # service slot right after the return.
    if await _vehicle_has_blocking_workload(db, vehicle.id):
        if body.scheduled_date.tzinfo is None:
            scheduled = body.scheduled_date.replace(tzinfo=UTC)
        else:
            scheduled = body.scheduled_date
        if scheduled <= datetime.now(tz=UTC):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle has active reservations — cancel or complete them first",
            )

    technician_id = await _resolve_technician(db, current_user, body.technician_id)

    order = ServiceOrder(
        vehicle_id=vehicle.id,
        type=body.type,
        status=ServiceOrderStatus.SCHEDULED,
        description=body.description,
        cost=body.cost,
        scheduled_date=body.scheduled_date,
        technician_id=technician_id,
    )
    order = await service_repository.create_order(db, order)

    # Flip the vehicle off the rental floor only if it's currently up for
    # grabs. Don't override RENTED — that would lie to the booking flow.
    if vehicle.status == VehicleStatus.AVAILABLE:
        vehicle.status = VehicleStatus.MAINTENANCE
        await vehicle_repository.update(db, vehicle)

    # Re-fetch with relationships eagerly loaded so the response DTO
    # doesn't trigger an implicit lazy-load (forbidden under async session).
    refreshed = await service_repository.get_order_by_id(db, order.id)
    assert refreshed is not None
    return refreshed


async def update_order(
    db: AsyncSession,
    current_user: User,
    order_id: uuid.UUID,
    body: ServiceOrderUpdate,
) -> ServiceOrder:
    order = await service_repository.get_order_by_id_for_update(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")

    _ensure_can_manage(current_user, order)

    if order.status == ServiceOrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot edit a completed service order",
        )

    payload = body.model_dump(exclude_unset=True)
    if "technician_id" in payload:
        payload["technician_id"] = await _resolve_technician(
            db, current_user, payload["technician_id"]
        )

    for key, value in payload.items():
        setattr(order, key, value)

    await service_repository.update_order(db, order)
    refreshed = await service_repository.get_order_by_id(db, order.id)
    assert refreshed is not None
    return refreshed


async def update_status(
    db: AsyncSession,
    current_user: User,
    order_id: uuid.UUID,
    body: ServiceOrderStatusUpdate,
) -> ServiceOrder:
    order = await service_repository.get_order_by_id_for_update(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")

    _ensure_can_manage(current_user, order)

    current = order.status
    target = body.status
    if target == current:
        # Idempotent no-op: returning 422 here would punish a benign retry.
        refreshed = await service_repository.get_order_by_id(db, order.id)
        assert refreshed is not None
        return refreshed

    if target not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Illegal transition: {current} -> {target}",
        )

    order.status = target
    if target == ServiceOrderStatus.COMPLETED:
        order.completed_date = datetime.now(tz=UTC)
        if body.cost is not None:
            order.cost = body.cost
        # Once this order is done, release the vehicle back to the catalog
        # — but only if no other open service work remains on it.
        await _release_vehicle_if_idle(db, order.vehicle_id)

    await service_repository.update_order(db, order)
    refreshed = await service_repository.get_order_by_id(db, order.id)
    assert refreshed is not None
    return refreshed


async def _release_vehicle_if_idle(db: AsyncSession, vehicle_id: uuid.UUID) -> None:
    """Flip the vehicle back to AVAILABLE once no open service work remains."""
    if await service_repository.has_active_service_for_vehicle(db, vehicle_id):
        return
    vehicle = await vehicle_repository.get_by_id_for_update(db, vehicle_id)
    if vehicle is None:
        return
    # Don't override OUT_OF_SERVICE / RENTED — only flip MAINTENANCE back.
    if vehicle.status == VehicleStatus.MAINTENANCE:
        vehicle.status = VehicleStatus.AVAILABLE
        await vehicle_repository.update(db, vehicle)


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> ServiceOrder:
    order = await service_repository.get_order_by_id(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")
    return order


async def list_orders(
    db: AsyncSession,
    current_user: User,
    params: ServiceOrderListParams,
) -> tuple[list[ServiceOrder], int]:
    # A technician only sees their own queue; admins see everything.
    technician_filter = params.technician_id
    if current_user.role == UserRole.TECHNICIAN:
        technician_filter = current_user.id

    return await service_repository.list_orders(
        db,
        offset=params.offset,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        status=params.status,
        vehicle_id=params.vehicle_id,
        technician_id=technician_filter,
        type_=params.type,
        scheduled_from=params.scheduled_from,
        scheduled_to=params.scheduled_to,
    )


async def get_stats(db: AsyncSession) -> ServiceOrderStats:
    counts = await service_repository.count_by_status(db)
    scheduled = counts.get(ServiceOrderStatus.SCHEDULED, 0)
    in_progress = counts.get(ServiceOrderStatus.IN_PROGRESS, 0)
    completed = counts.get(ServiceOrderStatus.COMPLETED, 0)
    return ServiceOrderStats(
        scheduled=scheduled,
        in_progress=in_progress,
        completed=completed,
        total=scheduled + in_progress + completed,
    )


async def list_vehicle_timeline(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[ServiceOrder]:
    """All service orders for a vehicle, newest scheduled first."""
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return await service_repository.list_orders_for_vehicle(db, vehicle_id)


async def add_history_entry(
    db: AsyncSession,
    current_user: User,
    body: ServiceHistoryCreate,
) -> ServiceOrder:
    """Attach a history entry to an order — typically used at completion time."""
    order = await service_repository.get_order_by_id_for_update(db, body.service_order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")

    _ensure_can_manage(current_user, order)

    if order.status == ServiceOrderStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Start the service order before recording work — move it to IN_PROGRESS first",
        )

    from app.models.service_history import ServiceHistory

    entry = ServiceHistory(
        vehicle_id=order.vehicle_id,
        service_order_id=order.id,
        notes=body.notes,
        parts_replaced=body.parts_replaced,
        mileage_at_service=body.mileage_at_service,
    )
    await service_repository.create_history(db, entry)

    refreshed = await service_repository.get_order_by_id(db, order.id)
    assert refreshed is not None
    return refreshed
