import pytest
from httpx import AsyncClient

from tests.conftest import register


@pytest.mark.asyncio
async def test_register_and_me(client: AsyncClient):
    data = await register(client)
    assert data["token_type"] == "bearer"
    assert data["user"]["display_name"] == "Nick"
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me = await client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["email"].startswith("nick-")
    assert body["timezone"] == "Asia/Kolkata"
    assert body["preferences"]["scoring_weights"]["tasks"] == 0.3


@pytest.mark.asyncio
async def test_duplicate_email(client: AsyncClient):
    first = await register(client, "dup")
    again = await client.post(
        "/api/v1/auth/register",
        json={
            "email": first["user"]["email"],
            "password": "correcthorse",
            "display_name": "Other",
            "timezone": "UTC",
        },
    )
    assert again.status_code == 409


@pytest.mark.asyncio
async def test_login_and_bad_password(client: AsyncClient):
    data = await register(client, "login")
    email = data["user"]["email"]
    ok = await client.post("/api/v1/auth/login", json={"email": email, "password": "correcthorse"})
    assert ok.status_code == 200
    bad = await client.post("/api/v1/auth/login", json={"email": email, "password": "wronghorse1"})
    assert bad.status_code == 401
    unknown = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "correcthorse"}
    )
    assert unknown.status_code == 401
    assert unknown.json()["error"]["message"] == bad.json()["error"]["message"]


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
