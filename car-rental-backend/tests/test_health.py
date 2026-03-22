import pytest


@pytest.mark.asyncio
async def test_root(client):
    # When
    response = await client.get("/")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "DriveEase" in data["message"]


@pytest.mark.asyncio
async def test_health_check(client):
    # When
    response = await client.get("/health")

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
