"""Repozytorium recenzji — kolekcja ``reviews`` w MongoDB.

Recenzje są nierelacyjne (treść komentarza, prywatność edycji, brak
referencji innych encji do nich), więc trzymamy je w Mongo zgodnie
z założeniem projektu z CLAUDE.md.

Unikalność per (rental_id, user_id) jest wymuszana przez compound
unique index — próba ponownego dodania opinii zwróci ``DuplicateKeyError``,
który serwis tłumaczy na HTTP 409.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

COLLECTION = "reviews"
UNIQUE_INDEX_NAME = "uq_reviews_rental_user"

# JSON Schema validator applied to the Mongo collection — equivalent of
# a CHECK constraint. Centralised here so the service layer can ensure the
# collection exists with the validator on startup.
_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "vehicle_id",
            "rental_id",
            "rating",
            "created_at",
            "author",
        ],
        "properties": {
            "user_id": {"bsonType": "string"},
            "vehicle_id": {"bsonType": "string"},
            "rental_id": {"bsonType": "string"},
            "rating": {"bsonType": "int", "minimum": 1, "maximum": 5},
            "comment": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
            "author": {
                "bsonType": "object",
                "required": ["id", "first_name", "last_name"],
                "properties": {
                    "id": {"bsonType": "string"},
                    "first_name": {"bsonType": "string"},
                    "last_name": {"bsonType": "string"},
                    "avatar_url": {"bsonType": ["string", "null"]},
                },
            },
        },
    }
}


async def ensure_collection(mongo: AsyncIOMotorDatabase[Any]) -> None:
    """Create the collection with validator + indexes if not already present.

    Safe to call on every startup: ``create_collection`` is a no-op when the
    collection already exists, and the index ops are idempotent. Existing
    collections get their validator updated via ``collMod`` so changes to the
    schema (e.g. tightening required fields) are picked up.
    """
    names = await mongo.list_collection_names(filter={"name": COLLECTION})
    if COLLECTION not in names:
        await mongo.create_collection(COLLECTION, validator=_VALIDATOR)
    else:
        await mongo.command({"collMod": COLLECTION, "validator": _VALIDATOR})

    coll = mongo[COLLECTION]
    await coll.create_index(
        [("rental_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name=UNIQUE_INDEX_NAME,
    )
    await coll.create_index([("vehicle_id", ASCENDING), ("created_at", DESCENDING)])
    await coll.create_index("user_id")


def _author_dict(
    *,
    user_id: uuid.UUID,
    first_name: str,
    last_name: str,
    avatar_url: str | None,
) -> dict[str, Any]:
    return {
        "id": str(user_id),
        "first_name": first_name,
        "last_name": last_name,
        "avatar_url": avatar_url,
    }


async def insert(
    mongo: AsyncIOMotorDatabase[Any],
    *,
    user_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    rental_id: uuid.UUID,
    rating: int,
    comment: str | None,
    author_first_name: str,
    author_last_name: str,
    author_avatar_url: str | None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "_id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "vehicle_id": str(vehicle_id),
        "rental_id": str(rental_id),
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(tz=UTC),
        "author": _author_dict(
            user_id=user_id,
            first_name=author_first_name,
            last_name=author_last_name,
            avatar_url=author_avatar_url,
        ),
    }
    await mongo[COLLECTION].insert_one(doc)
    return doc


async def list_all(
    mongo: AsyncIOMotorDatabase[Any],
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    coll = mongo[COLLECTION]
    total = await coll.count_documents({})
    cursor = coll.find({}).sort("created_at", DESCENDING).skip(offset).limit(limit)
    items = await cursor.to_list(length=limit)
    return items, total


async def get_by_id(
    mongo: AsyncIOMotorDatabase[Any], review_id: uuid.UUID
) -> dict[str, Any] | None:
    return await mongo[COLLECTION].find_one({"_id": str(review_id)})


async def find_and_delete_by_id(
    mongo: AsyncIOMotorDatabase[Any], review_id: uuid.UUID
) -> dict[str, Any] | None:
    """Atomically delete the review and return its previous state, or ``None``.

    Single round-trip equivalent of ``get_by_id`` + ``delete_one`` — eliminates
    the race window between the read and the delete when two admins concurrently
    moderate the same review.
    """
    result: dict[str, Any] | None = await mongo[COLLECTION].find_one_and_delete(
        {"_id": str(review_id)}
    )
    return result


async def list_user_rental_ids(
    mongo: AsyncIOMotorDatabase[Any], user_id: uuid.UUID
) -> list[str]:
    """Return rental IDs already reviewed by the given user.

    UI uses this to hide the "write review" affordance for rentals that the
    user has already reviewed. Returns raw strings (UUIDs are stored as
    strings in Mongo) so the service layer can convert them once.
    """
    coll = mongo[COLLECTION]
    cursor = coll.find({"user_id": str(user_id)}, {"rental_id": 1, "_id": 0})
    docs = await cursor.to_list(length=None)
    return [d["rental_id"] for d in docs]


async def list_for_vehicle(
    mongo: AsyncIOMotorDatabase[Any],
    vehicle_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    coll = mongo[COLLECTION]
    filt = {"vehicle_id": str(vehicle_id)}
    total = await coll.count_documents(filt)
    cursor = (
        coll.find(filt).sort("created_at", DESCENDING).skip(offset).limit(limit)
    )
    items = await cursor.to_list(length=limit)
    return items, total


async def aggregate_rating(
    mongo: AsyncIOMotorDatabase[Any], vehicle_id: uuid.UUID
) -> tuple[float | None, int]:
    """Recompute average rating and count for a vehicle from the source of truth."""
    pipeline: list[dict[str, Any]] = [
        {"$match": {"vehicle_id": str(vehicle_id)}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    results = await mongo[COLLECTION].aggregate(pipeline).to_list(1)
    if not results:
        return None, 0
    doc = results[0]
    return round(float(doc["avg"]), 2), int(doc["count"])
