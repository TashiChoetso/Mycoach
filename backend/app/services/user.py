from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidInput, Unauthorized
from app.core.security import verify_password
from app.models.user import User
from app.repositories.area import AreaRepository
from app.repositories.focus import FocusRepository
from app.repositories.user import UserRepository
from app.schemas import PreferencesUpdate, PriorityUpdate, UserOut, UserUpdate
from app.services.area import display_name, serialize_user
from app.services.focus import focus_name, local_today


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.areas = AreaRepository(db)
        self.focuses = FocusRepository(db)

    async def me(self, user: User) -> UserOut:
        selected = await self.areas.list_user_areas(user.id)
        full = await self.users.get_by_id(user.id)
        assert full is not None
        return serialize_user(full, selected)

    async def update(self, user: User, payload: UserUpdate) -> UserOut:
        if payload.display_name is not None:
            user.display_name = payload.display_name.strip()
        if payload.timezone is not None:
            try:
                ZoneInfo(payload.timezone)
            except ZoneInfoNotFoundError as exc:
                raise InvalidInput("Unknown timezone") from exc
            user.timezone = payload.timezone
        if payload.locale is not None:
            user.locale = payload.locale
        if payload.currency is not None:
            user.currency = payload.currency.upper()
        await self.db.commit()
        return await self.me(user)

    async def update_preferences(self, user: User, payload: PreferencesUpdate) -> UserOut:
        full = await self.users.get_by_id(user.id)
        assert full is not None and full.preferences is not None
        prefs = full.preferences
        if payload.theme is not None:
            prefs.theme = payload.theme
        if payload.week_starts_on is not None:
            prefs.week_starts_on = payload.week_starts_on
        if payload.scoring_weights is not None:
            if not payload.scoring_weights or any(v < 0 for v in payload.scoring_weights.values()):
                raise InvalidInput("Invalid scoring weights")
            prefs.scoring_weights = payload.scoring_weights
        if payload.dashboard_sections is not None:
            prefs.dashboard_sections = payload.dashboard_sections
        await self.db.commit()
        return await self.me(user)

    async def priorities(self, user: User) -> dict[str, str]:
        today = local_today(user)
        day_key = today.isoformat()
        month_key = today.strftime("%Y-%m")
        day = await self.users.get_priority(user.id, "day", day_key)
        month = await self.users.get_priority(user.id, "month", month_key)
        return {"day": day.text if day else "", "month": month.text if month else ""}

    async def set_priority(self, user: User, payload: PriorityUpdate) -> dict[str, str]:
        if payload.period not in {"day", "month"}:
            raise InvalidInput("period must be day or month")
        today = local_today(user)
        period_key = today.isoformat() if payload.period == "day" else today.strftime("%Y-%m")
        await self.users.upsert_priority(user.id, payload.period, period_key, payload.text.strip())
        await self.db.commit()
        return await self.priorities(user)

    async def complete_onboarding(self, user: User) -> UserOut:
        if user.onboarding_completed_at is None:
            user.onboarding_completed_at = datetime.now(UTC)
            await self.db.commit()
        return await self.me(user)

    async def export(self, user: User) -> dict:
        selected = await self.areas.list_user_areas(user.id)
        focuses = await self.focuses.list_user_focuses(user.id)
        logs = await self.focuses.logs_for_user(user.id)
        priorities = await self.users.list_priorities(user.id)
        full = await self.users.get_by_id(user.id)
        assert full is not None
        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "user": {
                "id": str(full.id),
                "email": full.email,
                "display_name": full.display_name,
                "timezone": full.timezone,
                "locale": full.locale,
                "currency": full.currency,
                "onboarding_completed_at": (
                    full.onboarding_completed_at.isoformat() if full.onboarding_completed_at else None
                ),
                "preferences": {
                    "theme": full.preferences.theme if full.preferences else None,
                    "week_starts_on": full.preferences.week_starts_on if full.preferences else None,
                },
            },
            "areas": [
                {
                    "id": str(item.id),
                    "name": display_name(item),
                    "slug": item.area.slug,
                    "is_enabled": item.is_enabled,
                }
                for item in selected
            ],
            "focuses": [
                {
                    "id": str(item.id),
                    "name": focus_name(item),
                    "kind": item.focus.kind,
                    "user_area_id": str(item.user_area_id),
                    "is_enabled": item.is_enabled,
                }
                for item in focuses
            ],
            "logs": [
                {
                    "user_focus_id": str(item.user_focus_id),
                    "date": item.log_date.isoformat(),
                    "status": item.status,
                    "value": float(item.value) if item.value is not None else None,
                    "note": item.note,
                }
                for item in logs
            ],
            "priorities": [
                {
                    "period": item.period,
                    "period_key": item.period_key,
                    "text": item.text,
                }
                for item in priorities
            ],
        }

    async def delete_account(self, user: User, password: str) -> None:
        if not verify_password(password, user.password_hash):
            raise Unauthorized("Password is incorrect")
        await self.users.delete_user(user)
        await self.db.commit()
