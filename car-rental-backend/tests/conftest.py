from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_db
from app.main import app


@pytest.fixture(autouse=True)
def mock_lifespan_services():
    """Prevent real Redis/MongoDB/PostgreSQL connections during tests."""
    with (
        patch("app.main.connect_mongo", new_callable=AsyncMock),
        patch("app.main.connect_redis", new_callable=AsyncMock),
        patch("app.main.close_redis", new_callable=AsyncMock),
        patch("app.main.close_mongo", new_callable=AsyncMock),
        patch("app.main.async_engine"),
    ):
        yield


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    return session


@pytest.fixture
async def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
