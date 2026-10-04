import pytest
from httpx import AsyncClient

from tests.conftest import register


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def select_health(client: AsyncClient, headers: dict) -> dict:
    catalog = (await client.get("/api/v1/areas", headers=headers)).json()["catalog"]
    health = next(item for item in catalog if item["slug"] == "health")
    created = await client.post("/api/v1/areas", headers=headers, json={"area_id": health["id"]})
    assert created.status_code == 201, created.text
    return created.json()


async def add_focus(client: AsyncClient, headers: dict, user_area_id: str, **payload) -> dict:
    body = {"user_area_id": user_area_id, "kind": "check", **payload}
    created = await client.post("/api/v1/focuses", headers=headers, json=body)
    assert created.status_code == 201, created.text
    return created.json()


async def add_health_practices(client: AsyncClient, headers: dict, area_id: str) -> dict[str, dict]:
    move = await add_focus(client, headers, area_id, name="Move")
    strength = await add_focus(client, headers, area_id, name="Strength")
    fuel = await add_focus(client, headers, area_id, name="Fuel")
    water = await add_focus(
        client, headers, area_id, name="Water", kind="count", target_value=8, unit="glasses"
    )
    return {"Move": move, "Strength": strength, "Fuel": fuel, "Water": water}


@pytest.mark.asyncio
async def test_health_starts_empty_until_user_adds_practices(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    await select_health(client, headers)

    today = await client.get("/api/v1/dashboard/today", headers=headers)
    assert today.status_code == 200, today.text
    payload = today.json()
    health = next(item for item in payload["areas"] if item["slug"] == "health")
    assert health["focuses"] == []
    assert payload["momentum"]["rest_day"] is True
    assert payload["week_days"]
    assert payload["priorities"] == {"day": "", "month": ""}


@pytest.mark.asyncio
async def test_health_gets_sub_practices_and_scores(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    area = await select_health(client, headers)
    await add_health_practices(client, headers, area["id"])

    today = await client.get("/api/v1/dashboard/today", headers=headers)
    assert today.status_code == 200, today.text
    payload = today.json()
    health = next(item for item in payload["areas"] if item["slug"] == "health")
    names = {item["name"] for item in health["focuses"]}
    assert {"Move", "Strength", "Fuel", "Water"} <= names
    assert payload["momentum"]["rest_day"] is False
    assert payload["momentum"]["score"] == 0
    move = next(item for item in health["focuses"] if item["name"] == "Move")
    assert len(move["marks"]) == 7

    water = next(item for item in health["focuses"] if item["name"] == "Water")

    done = await client.post(f"/api/v1/focuses/{move['id']}/complete", headers=headers, json={})
    assert done.status_code == 200, done.text
    board = done.json()["board"]
    health = next(item for item in board["areas"] if item["slug"] == "health")
    assert health["score"] == 25
    assert board["momentum"]["score"] == 25

    counted = await client.post(
        f"/api/v1/focuses/{water['id']}/complete", headers=headers, json={"value": 4}
    )
    assert counted.status_code == 200
    board = counted.json()["board"]
    health = next(item for item in board["areas"] if item["slug"] == "health")
    water_row = next(item for item in health["focuses"] if item["name"] == "Water")
    assert water_row["score"] == 50
    assert health["score"] == 38
    assert board["momentum"]["completed"] == 2


@pytest.mark.asyncio
async def test_skip_is_not_a_zero(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    area = await select_health(client, headers)
    practices = await add_health_practices(client, headers, area["id"])
    move = practices["Move"]
    others = [practices["Strength"], practices["Fuel"], practices["Water"]]
    await client.post(f"/api/v1/focuses/{move['id']}/complete", headers=headers, json={})
    for item in others:
        await client.post(f"/api/v1/focuses/{item['id']}/skip", headers=headers, json={})
    board = (await client.get("/api/v1/dashboard/today", headers=headers)).json()
    health = next(item for item in board["areas"] if item["slug"] == "health")
    assert health["score"] == 100
    assert board["momentum"]["score"] == 100


@pytest.mark.asyncio
async def test_custom_focus_on_custom_area(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    area = (
        await client.post("/api/v1/areas", headers=headers, json={"name": "Guitar"})
    ).json()
    today = (await client.get("/api/v1/dashboard/today", headers=headers)).json()
    guitar = next(item for item in today["areas"] if item["name"] == "Guitar")
    assert guitar["focuses"] == []
    created = await client.post(
        "/api/v1/focuses",
        headers=headers,
        json={"user_area_id": area["id"], "name": "Practice", "kind": "count", "target_value": 30, "unit": "min"},
    )
    assert created.status_code == 201, created.text
    logged = await client.post(
        f"/api/v1/focuses/{created.json()['id']}/complete", headers=headers, json={"value": 15}
    )
    assert logged.status_code == 200
    detail = await client.get(f"/api/v1/areas/{area['id']}", headers=headers)
    assert detail.status_code == 200
    practice = next(item for item in detail.json()["area"]["focuses"] if item["name"] == "Practice")
    assert practice["score"] == 50


@pytest.mark.asyncio
async def test_day_and_month_priority(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    saved = await client.put(
        "/api/v1/me/priority",
        headers=headers,
        json={"period": "day", "text": "Finish the lab"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["day"] == "Finish the lab"
    month = await client.put(
        "/api/v1/me/priority",
        headers=headers,
        json={"period": "month", "text": "Ship the portfolio"},
    )
    assert month.json()["month"] == "Ship the portfolio"
    today = (await client.get("/api/v1/dashboard/today", headers=headers)).json()
    assert today["priorities"]["day"] == "Finish the lab"
    assert today["priorities"]["month"] == "Ship the portfolio"
