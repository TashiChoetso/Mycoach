from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ["SECRET_KEY"] = "test-secret-key-not-for-prod-use-32chars!!"
os.environ["AUTH_RATE_LIMIT"] = "1000"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mycoach:mycoach@localhost:5433/mycoach_test",
)

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.db import Base  # noqa: E402
from app.core.seed import seed_catalog  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: F401,F403,E402


async def _prepare() -> None:
    admin_url = os.environ["DATABASE_URL"].rsplit("/", 1)[0] + "/postgres"
    admin = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = 'mycoach_test'"))
        if not exists:
            await conn.execute(text("CREATE DATABASE mycoach_test"))
    await admin.dispose()
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await seed_catalog(db)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    asyncio.run(_prepare())


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register(client: AsyncClient, suffix: str | None = None) -> dict:
    suffix = suffix or uuid.uuid4().hex[:8]
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"nick-{suffix}@example.com",
            "password": "correcthorse",
            "display_name": "Nick",
            "timezone": "Asia/Kolkata",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
