"""
Import all models here so Alembic can discover them via Base.metadata.
"""

from app.models.category import Category, CategoryName
from app.models.customer_note import CustomerNote
from app.models.incident import Incident, IncidentSeverity, IncidentType
from app.models.rental import Rental, RentalPriceBreakdown, Reservation, ReservationStatus
from app.models.service_history import ServiceHistory
from app.models.service_order import ServiceOrder, ServiceOrderStatus, ServiceType
from app.models.user import User, UserRole
from app.models.vehicle import EngineType, Vehicle, VehicleStatus
from app.models.vehicle_image import VehicleImage

__all__ = [
    "Category",
    "CategoryName",
    "CustomerNote",
    "EngineType",
    "Incident",
    "IncidentSeverity",
    "IncidentType",
    "Rental",
    "RentalPriceBreakdown",
    "Reservation",
    "ReservationStatus",
    "ServiceHistory",
    "ServiceOrder",
    "ServiceOrderStatus",
    "ServiceType",
    "User",
    "UserRole",
    "Vehicle",
    "VehicleImage",
    "VehicleStatus",
]
