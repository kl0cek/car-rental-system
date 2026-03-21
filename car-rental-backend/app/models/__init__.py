"""
Import all models here so Alembic can discover them via Base.metadata.
"""

from app.models.rental import Rental, RentalStatus
from app.models.user import User, UserRole
from app.models.vehicle import EngineType, Vehicle, VehicleStatus

__all__ = [
    "User",
    "UserRole",
    "Vehicle",
    "EngineType",
    "VehicleStatus",
    "Rental",
    "RentalStatus",
]
