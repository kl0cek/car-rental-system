"""
Import all models here so Alembic can discover them via Base.metadata.
"""

from app.models.category import Category, CategoryName
from app.models.rental import Rental, RentalPriceBreakdown, Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.models.vehicle import EngineType, Vehicle, VehicleStatus

__all__ = [
    "Category",
    "CategoryName",
    "EngineType",
    "Rental",
    "RentalPriceBreakdown",
    "Reservation",
    "ReservationStatus",
    "User",
    "UserRole",
    "Vehicle",
    "VehicleStatus",
]
