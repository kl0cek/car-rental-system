"""Idempotentny init kolekcji MongoDB.

Tworzy / aktualizuje walidatory ``$jsonSchema`` i indeksy kolekcji, których
strukturę chcemy mieć pod kontrolą. Wywoływany ręcznie / z pipeline'u
deploy'owego — NIE z ``lifespan`` aplikacji, żeby aplikacja mogła działać
z użytkownikiem Mongo bez uprawnień do ``collMod``.

Użycie:
    python -m scripts.init_mongo
"""

import asyncio

from app.db.mongodb import close_mongo, connect_mongo, get_mongo_db
from app.repositories import review_repository


async def main() -> None:
    await connect_mongo()
    try:
        mongo_db = get_mongo_db()
        await review_repository.ensure_collection(mongo_db)
        print("[MONGO] reviews: validator + indexes ensured")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
