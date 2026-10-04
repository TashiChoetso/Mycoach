from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.area import Area, UserArea


class AreaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_system(self) -> list[Area]:
        result = await self.db.execute(
            select(Area).where(Area.is_system.is_(True)).order_by(Area.sort_order, Area.name)
        )
        return list(result.scalars().all())

    async def get_area(self, area_id: uuid.UUID) -> Area | None:
        result = await self.db.execute(select(Area).where(Area.id == area_id))
        return result.scalar_one_or_none()

    async def get_system_by_slug(self, slug: str) -> Area | None:
        result = await self.db.execute(select(Area).where(Area.slug == slug, Area.is_system.is_(True)))
        return result.scalar_one_or_none()

    async def list_user_areas(self, user_id: uuid.UUID) -> list[UserArea]:
        result = await self.db.execute(
            select(UserArea)
            .options(selectinload(UserArea.area))
            .where(UserArea.user_id == user_id)
            .order_by(UserArea.sort_order, UserArea.created_at)
        )
        return list(result.scalars().all())

    async def get_user_area(self, user_id: uuid.UUID, user_area_id: uuid.UUID) -> UserArea | None:
        result = await self.db.execute(
            select(UserArea)
            .options(selectinload(UserArea.area))
            .where(UserArea.id == user_area_id, UserArea.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_membership(self, user_id: uuid.UUID, area_id: uuid.UUID) -> UserArea | None:
        result = await self.db.execute(
            select(UserArea).where(UserArea.user_id == user_id, UserArea.area_id == area_id)
        )
        return result.scalar_one_or_none()

    async def custom_name_taken(self, user_id: uuid.UUID, name: str) -> bool:
        result = await self.db.execute(
            select(Area).where(Area.owner_user_id == user_id, Area.name.ilike(name))
        )
        return result.scalar_one_or_none() is not None

    async def add_area(self, area: Area) -> Area:
        self.db.add(area)
        await self.db.flush()
        return area

    async def add_user_area(self, user_area: UserArea) -> UserArea:
        self.db.add(user_area)
        await self.db.flush()
        return user_area

    async def delete_user_area(self, user_area: UserArea) -> None:
        await self.db.delete(user_area)
