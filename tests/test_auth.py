
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from config import settings


pytestmark = pytest.mark.asyncio


# =========================================================
# Registration Tests
# =========================================================

async def test_register_success(client):
    email = f"auth_test_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Test12345",
            "confirm_password": "Test12345",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "customer"


async def test_register_duplicate_email(client):
    email = f"duplicate_auth_{uuid.uuid4().hex}@example.com"

    user_data = {
        "email": email,
        "password": "Test12345",
        "confirm_password": "Test12345",
    }

    # First registration should succeed
    first_response = await client.post(
        "/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201

    # Second registration with the same email should fail
    second_response = await client.post(
        "/auth/register",
        json=user_data,
    )

    assert second_response.status_code == 409


async def test_register_password_mismatch(client):
    email = f"mismatch_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Test12345",
            "confirm_password": "Different123",
        },
    )

    assert response.status_code == 422


async def test_register_password_too_short(client):
    email = f"short_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Ab1",
            "confirm_password": "Ab1",
        },
    )

    assert response.status_code == 422


async def test_register_password_without_lowercase(client):
    email = f"uppercase_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TEST12345",
            "confirm_password": "TEST12345",
        },
    )

    assert response.status_code == 422


async def test_register_password_without_digit(client):
    email = f"nodigit_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword",
            "confirm_password": "TestPassword",
        },
    )

    assert response.status_code == 422


async def test_register_missing_confirm_password(client):
    email = f"missing_confirm_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Test12345",
        },
    )

    assert response.status_code == 422


async def test_register_invalid_email(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "Test12345",
            "confirm_password": "Test12345",
        },
    )

    assert response.status_code == 422


# =========================================================
# Login Tests
# =========================================================

async def test_login_success(client):
    email = f"login_test_{uuid.uuid4().hex}@example.com"
    password = "Test12345"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )

    assert register_response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    email = f"wrong_password_{uuid.uuid4().hex}@example.com"
    password = "Correct123"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )

    assert register_response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Wrong123",
        },
    )

    assert response.status_code == 401


async def test_login_nonexistent_user(client):
    email = f"nonexistent_{uuid.uuid4().hex}@example.com"

    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Some123",
        },
    )

    assert response.status_code == 401


async def test_login_invalid_email(client):
    response = await client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "Some123",
        },
    )

    assert response.status_code == 422


async def test_login_password_too_short(client):
    response = await client.post(
        "/auth/login",
        json={
            "email": "valid@example.com",
            "password": "Ab1",
        },
    )

    assert response.status_code == 422


# =========================================================
# Authentication / JWT Tests
# =========================================================

async def test_me_without_token(client):
    response = await client.get("/auth/me")

    assert response.status_code == 401


async def test_me_with_malformed_token(client):
    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer this-is-not-a-valid-jwt",
        },
    )

    assert response.status_code == 401


async def test_me_with_valid_token(client, auth_token):
    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {auth_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert "email" in data
    assert "role" in data


async def test_me_with_expired_token(client, test_user):
    expired_payload = {
        "sub": str(test_user.id),
        "role": test_user.role.value,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401


async def test_me_with_invalid_signature(client, test_user):
    payload = {
        "sub": str(test_user.id),
        "role": test_user.role.value,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    invalid_token = jwt.encode(
        payload,
        "this-is-a-completely-wrong-secret-key-for-testing",
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {invalid_token}",
        },
    )

    assert response.status_code == 401


async def test_me_with_missing_subject(client, test_user):
    payload = {
        "role": test_user.role.value,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


# =========================================================
# Authorization Tests
# =========================================================

async def test_admin_check_customer_forbidden(client, auth_token):
    response = await client.get(
        "/auth/admin-check",
        headers={
            "Authorization": f"Bearer {auth_token}",
        },
    )

    assert response.status_code == 403


async def test_admin_check_without_token(client):
    response = await client.get("/auth/admin-check")

    assert response.status_code == 401
