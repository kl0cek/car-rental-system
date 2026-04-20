from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.db.engine import async_engine
from app.db.mongodb import close_mongo, connect_mongo
from app.db.redis import close_redis, connect_redis
from app.db.session import DbSession
from app.routers import admin, auth, rentals, reservations, users, vehicles
from app.services.user_service import AVATAR_UPLOAD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await connect_mongo()
    await connect_redis()
    yield
    await close_redis()
    await close_mongo()
    await async_engine.dispose()


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

app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(reservations.router)
app.include_router(rentals.router)
app.include_router(users.router)
app.include_router(admin.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
async def health_check(db: DbSession) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "healthy"}
