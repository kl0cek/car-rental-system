from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.engine import async_engine
from app.db.mongodb import close_mongo, connect_mongo
from app.db.redis import close_redis, connect_redis
from app.db.session import DbSession
from app.routers import auth, rentals, reservations, vehicles


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


app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(reservations.router)
app.include_router(rentals.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
async def health_check(db: DbSession) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "healthy"}
