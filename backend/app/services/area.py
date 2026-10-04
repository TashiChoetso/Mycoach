from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, InvalidInput, NotFound
from app.models.area import Area, UserArea
from app.models.user import User
from app.repositories.area import AreaRepository
from app.repositories.event import EventRepository
from app.schemas import (
    AreaCreate,
    AreaUpdate,
    AreasResponse,
    CatalogAreaOut,
    PreferencesOut,
    SelectedAreaOut,
    UserOut,
)


def display_name(user_area: UserArea) -> str:
    return user_area.custom_name or user_area.area.name


def serialize_selected(user_area: UserArea) -> SelectedAreaOut:
    return SelectedAreaOut(
        id=str(user_area.id),
        area_id=str(user_area.area_id),
        name=display_name(user_area),
        slug=user_area.area.slug,
        is_custom=not user_area.area.is_system,
        is_enabled=user_area.is_enabled,
        dashboard_visible=user_area.dashboard_visible,
        sort_order=user_area.sort_order,
        icon=user_area.area.icon,
    )


def serialize_user(user: User, selected: list[UserArea]) -> UserOut:
    prefs = user.preferences
    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        timezone=user.timezone,
        locale=user.locale,
        currency=user.currency,
        onboarding_completed_at=(
            user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None
        ),
        preferences=PreferencesOut.model_validate(prefs) if prefs else None,
        areas=[serialize_selected(item) for item in selected if item.area],
    )


class AreaService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.areas = AreaRepository(db)
        self.events = EventRepository(db)

    async def list(self, user: User) -> AreasResponse:
        catalog = await self.areas.list_system()
        selected = await self.areas.list_user_areas(user.id)
        selected_ids = {item.area_id for item in selected}
        return AreasResponse(
            catalog=[
                CatalogAreaOut(
                    id=str(area.id),
                    slug=area.slug,
                    name=area.name,
                    icon=area.icon,
                    selected=area.id in selected_ids,
                )
                for area in catalog
            ],
            selected=[serialize_selected(item) for item in selected],
        )

    async def create(self, user: User, payload: AreaCreate) -> SelectedAreaOut:
        if payload.area_id:
            return await self._select_catalog(user, uuid.UUID(payload.area_id))
        if not payload.name:
            raise InvalidInput("Provide an area_id or a custom name")
        return await self._create_custom(user, payload.name.strip(), payload.description)

    async def update(self, user: User, user_area_id: uuid.UUID, payload: AreaUpdate) -> SelectedAreaOut:
        user_area = await self.areas.get_user_area(user.id, user_area_id)
        if user_area is None:
            raise NotFound()
        if payload.custom_name is not None:
            user_area.custom_name = payload.custom_name.strip()
        if payload.is_enabled is not None:
            user_area.is_enabled = payload.is_enabled
        if payload.dashboard_visible is not None:
            user_area.dashboard_visible = payload.dashboard_visible
        if payload.sort_order is not None:
            user_area.sort_order = payload.sort_order
        await self.db.commit()
        user_area = await self.areas.get_user_area(user.id, user_area_id)
        assert user_area is not None
        return serialize_selected(user_area)

    async def delete(self, user: User, user_area_id: uuid.UUID) -> None:
        user_area = await self.areas.get_user_area(user.id, user_area_id)
        if user_area is None:
            raise NotFound()
        await self.areas.delete_user_area(user_area)
        await self.db.commit()

    async def _select_catalog(self, user: User, area_id: uuid.UUID) -> SelectedAreaOut:
        area = await self.areas.get_area(area_id)
        if area is None or not area.is_system:
            raise NotFound("Unknown area")
        existing = await self.areas.get_membership(user.id, area.id)
        if existing:
            raise Conflict("This area is already part of your life map")
        selected = await self.areas.list_user_areas(user.id)
        user_area = UserArea(user_id=user.id, area_id=area.id, sort_order=len(selected))
        await self.areas.add_user_area(user_area)
        user_area = await self.areas.get_user_area(user.id, user_area.id)
        assert user_area is not None
        from app.services.focus import FocusService

        await FocusService(self.db).ensure_for_user_area(user, user_area)
        await self.events.emit(
            user_id=user.id,
            event_type="AREA_SELECTED",
            entity_type="area",
            entity_id=area.id,
            metadata={"name": area.name},
        )
        await self.db.commit()
        user_area = await self.areas.get_user_area(user.id, user_area.id)
        assert user_area is not None
        return serialize_selected(user_area)

    async def _create_custom(self, user: User, name: str, description: str | None) -> SelectedAreaOut:
        if await self.areas.custom_name_taken(user.id, name):
            raise Conflict("You already have an area with this name")
        area = Area(
            name=name,
            description=description,
            is_system=False,
            owner_user_id=user.id,
            icon="sparkle",
        )
        await self.areas.add_area(area)
        selected = await self.areas.list_user_areas(user.id)
        user_area = UserArea(user_id=user.id, area_id=area.id, sort_order=len(selected))
        await self.areas.add_user_area(user_area)
        user_area = await self.areas.get_user_area(user.id, user_area.id)
        assert user_area is not None
        from app.services.focus import FocusService

        await FocusService(self.db).ensure_for_user_area(user, user_area)
        await self.events.emit(
            user_id=user.id,
            event_type="AREA_CREATED",
            entity_type="area",
            entity_id=area.id,
            metadata={"name": name, "is_custom": True},
        )
        await self.db.commit()
        user_area = await self.areas.get_user_area(user.id, user_area.id)
        assert user_area is not None
        return serialize_selected(user_area)
