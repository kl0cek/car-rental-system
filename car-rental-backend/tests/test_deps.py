import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.deps import CurrentUser, get_current_user, require_roles
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.models.user import User, UserRole


def _make_user(
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
) -> User:
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        first_name="Test",
        last_name="User",
        role=role,
        is_active=is_active,
    )
    user.id = uuid.uuid4()
    return user


def _build_app() -> FastAPI:
    """Minimal app with test endpoints using RBAC deps."""
    test_app = FastAPI()

    @test_app.get("/me")
    async def me(current_user: CurrentUser):
        return {"id": str(current_user.id), "role": current_user.role}

    @test_app.get(
        "/admin-only",
        dependencies=[Depends(require_roles(UserRole.ADMIN))],
    )
    async def admin_only():
        return {"ok": True}

    @test_app.get(
        "/staff",
        dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.EMPLOYEE))],
    )
    async def staff():
        return {"ok": True}

    @test_app.get(
        "/technician",
        dependencies=[Depends(require_roles(UserRole.TECHNICIAN))],
    )
    async def technician():
        return {"ok": True}

    return test_app


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.exists.return_value = 0
    return redis


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_returns_user_for_valid_token(self, mock_db, mock_redis):
        user = _make_user()
        token = create_access_token(str(user.id), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        assert resp.json()["id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_rejects_missing_token(self, mock_db):
        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/me")

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rejects_blacklisted_token(self, mock_db, mock_redis):
        mock_redis.exists.return_value = 1
        token = create_access_token(str(uuid.uuid4()), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.core.deps.get_redis", return_value=mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401
        assert "revoked" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self, mock_db, mock_redis):
        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.core.deps.get_redis", return_value=mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get(
                    "/me", headers={"Authorization": "Bearer invalid.token.here"}
                )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_refresh_token_as_access(self, mock_db, mock_redis):
        token = create_refresh_token(str(uuid.uuid4()), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.core.deps.get_redis", return_value=mock_redis):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401
        assert "token type" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_rejects_inactive_user(self, mock_db, mock_redis):
        user = _make_user(is_active=False)
        token = create_access_token(str(user.id), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401
        assert "inactive" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_user(self, mock_db, mock_redis):
        token = create_access_token(str(uuid.uuid4()), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=None)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401


class TestRequireRoles:
    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoint(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.ADMIN)
        token = create_access_token(str(user.id), UserRole.ADMIN)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get(
                    "/admin-only", headers={"Authorization": f"Bearer {token}"}
                )

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_customer_cannot_access_admin_endpoint(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.CUSTOMER)
        token = create_access_token(str(user.id), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get(
                    "/admin-only", headers={"Authorization": f"Bearer {token}"}
                )

        assert resp.status_code == 403
        assert "permissions" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_employee_can_access_staff_endpoint(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.EMPLOYEE)
        token = create_access_token(str(user.id), UserRole.EMPLOYEE)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/staff", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_access_staff_endpoint(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.ADMIN)
        token = create_access_token(str(user.id), UserRole.ADMIN)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get("/staff", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_customer_cannot_access_technician_endpoint(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.CUSTOMER)
        token = create_access_token(str(user.id), UserRole.CUSTOMER)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get(
                    "/technician", headers={"Authorization": f"Bearer {token}"}
                )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_technician_can_access_technician_endpoint(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.TECHNICIAN)
        token = create_access_token(str(user.id), UserRole.TECHNICIAN)

        app = _build_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        with (
            patch("app.core.deps.get_redis", return_value=mock_redis),
            patch("app.core.deps.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get(
                    "/technician", headers={"Authorization": f"Bearer {token}"}
                )

        assert resp.status_code == 200
