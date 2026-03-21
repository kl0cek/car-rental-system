import pytest
from jose import jwt

from app.config import settings
from app.core.exceptions import InvalidTokenError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import UserRole


class TestPassword:
    def test_hash_password_returns_bcrypt_hash(self):
        hashed = hash_password("secret123")
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestCreateAccessToken:
    def test_contains_correct_claims(self):
        token = create_access_token("user-123", UserRole.CUSTOMER)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert payload["role"] == "customer"
        assert "exp" in payload

    def test_admin_role_in_token(self):
        token = create_access_token("admin-1", UserRole.ADMIN)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert payload["role"] == "admin"

    def test_employee_role_in_token(self):
        token = create_access_token("emp-1", UserRole.EMPLOYEE)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert payload["role"] == "employee"

    def test_technician_role_in_token(self):
        token = create_access_token("tech-1", UserRole.TECHNICIAN)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert payload["role"] == "technician"


class TestCreateRefreshToken:
    def test_contains_correct_claims(self):
        token = create_refresh_token("user-456", UserRole.CUSTOMER)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
        assert payload["role"] == "customer"
        assert "exp" in payload


class TestDecodeToken:
    def test_decode_valid_token(self):
        token = create_access_token("user-789", UserRole.CUSTOMER)
        payload = decode_token(token)

        assert payload["sub"] == "user-789"
        assert payload["type"] == "access"
        assert payload["role"] == "customer"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(InvalidTokenError):
            decode_token("not.a.valid.token")

    def test_decode_tampered_token_raises(self):
        token = create_access_token("user-1", UserRole.CUSTOMER)
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(InvalidTokenError):
            decode_token(tampered)

    def test_decode_token_wrong_secret_raises(self):
        payload = {"sub": "user-1", "type": "access"}
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(InvalidTokenError):
            decode_token(token)
