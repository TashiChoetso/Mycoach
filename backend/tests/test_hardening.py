from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.core.rate_limit import reset_rate_limits
from tests.conftest import register


@pytest.fixture(autouse=True)
def _clear_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.mark.asyncio
async def test_health_reports_database(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"


@pytest.mark.asyncio
async def test_password_reset_and_login(client: AsyncClient):
    data = await register(client, "reset")
    email = data["user"]["email"]
    forgot = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    token = forgot.json()["reset_token"]
    assert token

    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "newhorseword"},
    )
    assert reset.status_code == 204

    bad = await client.post("/api/v1/auth/login", json={"email": email, "password": "correcthorse"})
    assert bad.status_code == 401
    ok = await client.post("/api/v1/auth/login", json={"email": email, "password": "newhorseword"})
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_export_and_delete_account(client: AsyncClient):
    data = await register(client, "export")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    exported = await client.get("/api/v1/me/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["user"]["email"].startswith("nick-")

    deleted = await client.request(
        "DELETE",
        "/api/v1/me",
        headers=headers,
        json={"password": "correcthorse"},
    )
    assert deleted.status_code == 204
    me = await client.get("/api/v1/me", headers=headers)
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_cannot_log_future_or_ancient_dates(client: AsyncClient):
    data = await register(client, "dates")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    catalog = (await client.get("/api/v1/areas", headers=headers)).json()["catalog"]
    health = next(item for item in catalog if item["slug"] == "health")
    area = await client.post("/api/v1/areas", headers=headers, json={"area_id": health["id"]})
    focus = await client.post(
        "/api/v1/focuses",
        headers=headers,
        json={"user_area_id": area.json()["id"], "name": "Move", "kind": "check"},
    )
    focus_id = focus.json()["id"]
    future = (date.today() + timedelta(days=2)).isoformat()
    past = (date.today() - timedelta(days=40)).isoformat()

    future_res = await client.post(
        f"/api/v1/focuses/{focus_id}/complete",
        headers=headers,
        json={"date": future},
    )
    assert future_res.status_code == 422

    past_res = await client.post(
        f"/api/v1/focuses/{focus_id}/complete",
        headers=headers,
        json={"date": past},
    )
    assert past_res.status_code == 422


@pytest.mark.asyncio
async def test_auth_rate_limit(client: AsyncClient, monkeypatch):
    from app.core import config

    monkeypatch.setenv("AUTH_RATE_LIMIT", "3")
    config.get_settings.cache_clear()
    reset_rate_limits()

    # Re-bind settings used by the auth router
    import app.api.v1.auth as auth_api

    auth_api.settings = config.get_settings()

    for _ in range(3):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wronghorse1"},
        )
        assert res.status_code == 401

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wronghorse1"},
    )
    assert blocked.status_code == 429

    monkeypatch.setenv("AUTH_RATE_LIMIT", "1000")
    config.get_settings.cache_clear()
    auth_api.settings = config.get_settings()
    reset_rate_limits()
