import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, Path, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import require_roles
from app.db.mongodb import get_mongo_db
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.schemas.rental import PickupRequest, RentalResponse, ReturnRequest
from app.services import rental_service

router = APIRouter(prefix="/rentals", tags=["rentals"])

EmployeeOrAdmin = Annotated[User, Depends(require_roles(UserRole.EMPLOYEE, UserRole.ADMIN))]
MongoDep = Annotated[AsyncIOMotorDatabase[Any], Depends(get_mongo_db)]


@router.post("/{reservation_id}/pickup", status_code=status.HTTP_201_CREATED)
async def pickup_rental(
    reservation_id: Annotated[uuid.UUID, Path()],
    body: PickupRequest,
    db: DbSession,
    current_user: EmployeeOrAdmin,
    mongo: MongoDep,
    background_tasks: BackgroundTasks,
) -> RentalResponse:
    rental = await rental_service.pickup_rental(db, current_user, reservation_id, body)
    background_tasks.add_task(
        rental_service.log_pickup,
        mongo,
        rental.id,
        reservation_id,
        current_user.id,
        body.photo_urls,
        body.client_signature_url,
    )
    return RentalResponse.model_validate(rental)


@router.post("/{rental_id}/return")
async def return_rental(
    rental_id: Annotated[uuid.UUID, Path()],
    body: ReturnRequest,
    db: DbSession,
    current_user: EmployeeOrAdmin,
    mongo: MongoDep,
    background_tasks: BackgroundTasks,
) -> RentalResponse:
    rental = await rental_service.return_rental(db, current_user, rental_id, body)
    background_tasks.add_task(
        rental_service.log_return,
        mongo,
        rental.id,
        rental.reservation_id,
        current_user.id,
        body.damage_photo_urls,
    )
    return RentalResponse.model_validate(rental)
