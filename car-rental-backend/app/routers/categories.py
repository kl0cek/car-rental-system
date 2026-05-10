"""Router katalogu kategorii pojazdów (`/categories`).

Read-only — kategorie zarządzane są przez seed/migracje. Frontend
potrzebuje `id` kategorii do tworzenia / aktualizacji pojazdów, więc
pełna lista z mnożnikami jest publiczna.
"""

from fastapi import APIRouter
from sqlalchemy import select

from app.db.session import DbSession
from app.models.category import Category
from app.schemas.vehicle import CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: DbSession) -> list[CategoryResponse]:
    result = await db.execute(select(Category).order_by(Category.name))
    return [CategoryResponse.model_validate(c) for c in result.scalars()]
