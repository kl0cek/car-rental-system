"""Punkt wejścia aplikacji FastAPI.

Tworzy instancję FastAPI, konfiguruje CORS, montuje katalogi statyczne
(awatary, zdjęcia pojazdów), rejestruje routery oraz zarządza cyklem życia
połączeń do MongoDB, Redisa i puli SQLAlchemy.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.bootstrap import apply_schema
from app.db.engine import close_db, connect_db
from app.db.mongodb import close_mongo, connect_mongo
from app.db.redis import close_redis, connect_redis
from app.db.session import DbSession
from app.routers import (
    admin,
    admin_customers,
    admin_vehicles,
    auth,
    categories,
    pricing,
    rentals,
    reservations,
    reviews,
    service_orders,
    users,
    vehicles,
)
from app.services.user_service import AVATAR_UPLOAD_DIR
from app.services.vehicle_service import VEHICLE_IMAGE_UPLOAD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Połączenia do Postgresa/Mongo/Redisa otwieramy raz na start procesu
    # i zwalniamy przy shutdownie — pula asyncpg żyje tyle co aplikacja.
    # Schemat relacyjny (schema.sql) stosujemy idempotentnie po podłączeniu puli.
    await connect_db()
    await apply_schema()
    await connect_mongo()
    await connect_redis()
    yield
    await close_redis()
    await close_mongo()
    await close_db()


# root_path="/api" bo nginx montuje backend pod tym prefiksem —
# dzięki temu OpenAPI generuje poprawne URL-e w /docs
app = FastAPI(
    title=settings.APP_NAME,
    root_path="/api",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/static/avatars",
    StaticFiles(directory=Path(AVATAR_UPLOAD_DIR)),
    name="avatars",
)

VEHICLE_IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/static/vehicles",
    StaticFiles(directory=Path(VEHICLE_IMAGE_UPLOAD_DIR)),
    name="vehicle_images",
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(vehicles.router)
app.include_router(reservations.router)
app.include_router(rentals.router)
app.include_router(pricing.router)
app.include_router(reviews.router)
app.include_router(service_orders.router)
app.include_router(service_orders.vehicle_router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(admin_vehicles.router)
app.include_router(admin_customers.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
async def health_check(db: DbSession) -> dict[str, str]:
    await db.fetchval("SELECT 1")
    return {"status": "healthy"}
