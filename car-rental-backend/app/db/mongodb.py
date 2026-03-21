from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

mongo_client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None


def get_mongo_db() -> AsyncIOMotorDatabase:
    if mongo_db is None:
        raise RuntimeError("MongoDB is not initialized. Call connect_mongo() first.")
    return mongo_db


async def connect_mongo() -> None:
    global mongo_client, mongo_db
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongo_db = mongo_client.get_default_database()


async def close_mongo() -> None:
    global mongo_client, mongo_db
    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None
        mongo_db = None
