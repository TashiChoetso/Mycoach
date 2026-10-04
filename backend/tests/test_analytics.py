import pytest
from httpx import AsyncClient

from tests.conftest import register
from tests.test_focuses import add_focus, auth, select_health


@pytest.mark.asyncio
async def test_progress_week_month_and_chart_series(client: AsyncClient):
    data = await register(client)
    headers = auth(data["access_token"])
    area = await select_health(client, headers)
    move = await add_focus(client, headers, area["id"], name="Move")
    await client.post(f"/api/v1/focuses/{move['id']}/complete", headers=headers, json={})

    week = await client.get("/api/v1/analytics/progress?range=week", headers=headers)
    assert week.status_code == 200, week.text
    body = week.json()
    assert body["range"] == "week"
    assert len(body["days"]) == 7
    assert len(body["weeks"]) == 8
    assert body["summary"]["completed"] >= 1
    assert any(day["completed"] >= 1 for day in body["days"])

    month = await client.get("/api/v1/analytics/progress?range=month", headers=headers)
    assert month.status_code == 200
    month_body = month.json()
    assert month_body["calendar"]
    assert month_body["series"]
    assert any(area["name"] == "Health & Fitness" for area in month_body["areas"])

    day = await client.get("/api/v1/analytics/progress?range=day", headers=headers)
    assert day.status_code == 200
    assert day.json()["days"][0]["areas"]
