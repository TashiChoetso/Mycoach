import pytest
from httpx import AsyncClient

from tests.conftest import register


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_catalog_and_select_area(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    listed = await client.get("/api/v1/areas", headers=headers)
    assert listed.status_code == 200
    catalog = listed.json()["catalog"]
    assert any(item["slug"] == "health" for item in catalog)
    health = next(item for item in catalog if item["slug"] == "health")
    created = await client.post("/api/v1/areas", headers=headers, json={"area_id": health["id"]})
    assert created.status_code == 201
    assert created.json()["name"] == "Health & Fitness"
    again = await client.post("/api/v1/areas", headers=headers, json={"area_id": health["id"]})
    assert again.status_code == 409


@pytest.mark.asyncio
async def test_custom_area(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    created = await client.post(
        "/api/v1/areas", headers=headers, json={"name": "Photography", "description": "Make pictures"}
    )
    assert created.status_code == 201
    body = created.json()
    assert body["is_custom"] is True
    assert body["name"] == "Photography"
    listed = await client.get("/api/v1/areas", headers=headers)
    names = [item["name"] for item in listed.json()["selected"]]
    assert "Photography" in names


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_area(client: AsyncClient):
    nick = await register(client, "nickiso")
    ada = await register(client, "adaiso")
    nick_headers = auth(nick["access_token"])
    ada_headers = auth(ada["access_token"])
    created = await client.post("/api/v1/areas", headers=nick_headers, json={"name": "Guitar"})
    area_id = created.json()["id"]
    stolen = await client.delete(f"/api/v1/areas/{area_id}", headers=ada_headers)
    assert stolen.status_code == 404
    still = await client.get("/api/v1/areas", headers=nick_headers)
    assert any(item["id"] == area_id for item in still.json()["selected"])


@pytest.mark.asyncio
async def test_today_hides_finance_until_selected(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    today = await client.get("/api/v1/dashboard/today", headers=headers)
    assert today.status_code == 200
    payload = today.json()
    assert payload["finance"] is None
    assert payload["momentum"]["rest_day"] is True
    catalog = (await client.get("/api/v1/areas", headers=headers)).json()["catalog"]
    finance = next(item for item in catalog if item["slug"] == "finance")
    await client.post("/api/v1/areas", headers=headers, json={"area_id": finance["id"]})
    today2 = await client.get("/api/v1/dashboard/today", headers=headers)
    assert today2.json()["finance"] is not None
    assert any(area["slug"] == "finance" for area in today2.json()["areas"])
    assert today2.json()["greeting"]["name"] == "Nick"
