from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.focus import Focus, FocusLog, UserFocus
from app.models.metrics import AreaScore, DailyScore


class FocusRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_system_for_area(self, area_id: uuid.UUID) -> list[Focus]:
        result = await self.db.execute(
            select(Focus)
            .where(Focus.area_id == area_id, Focus.is_system.is_(True))
            .order_by(Focus.sort_order, Focus.name)
        )
        return list(result.scalars().all())

    async def get_system_by_slug(self, slug: str) -> Focus | None:
        result = await self.db.execute(select(Focus).where(Focus.slug == slug, Focus.is_system.is_(True)))
        return result.scalar_one_or_none()

    async def list_user_focuses(self, user_id: uuid.UUID, user_area_id: uuid.UUID | None = None) -> list[UserFocus]:
        stmt = (
            select(UserFocus)
            .options(selectinload(UserFocus.focus), selectinload(UserFocus.user_area))
            .where(UserFocus.user_id == user_id)
            .order_by(UserFocus.sort_order, UserFocus.created_at)
        )
        if user_area_id is not None:
            stmt = stmt.where(UserFocus.user_area_id == user_area_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_focus(self, user_id: uuid.UUID, user_focus_id: uuid.UUID) -> UserFocus | None:
        result = await self.db.execute(
            select(UserFocus)
            .options(selectinload(UserFocus.focus), selectinload(UserFocus.user_area))
            .where(UserFocus.id == user_focus_id, UserFocus.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_membership(self, user_id: uuid.UUID, focus_id: uuid.UUID) -> UserFocus | None:
        result = await self.db.execute(
            select(UserFocus).where(UserFocus.user_id == user_id, UserFocus.focus_id == focus_id)
        )
        return result.scalar_one_or_none()

    async def add_focus(self, focus: Focus) -> Focus:
        self.db.add(focus)
        await self.db.flush()
        return focus

    async def add_user_focus(self, user_focus: UserFocus) -> UserFocus:
        self.db.add(user_focus)
        await self.db.flush()
        return user_focus

    async def delete_user_focus(self, user_focus: UserFocus) -> None:
        await self.db.delete(user_focus)

    async def logs_for_dates(self, user_id: uuid.UUID, dates: list[date]) -> list[FocusLog]:
        if not dates:
            return []
        result = await self.db.execute(
            select(FocusLog).where(FocusLog.user_id == user_id, FocusLog.log_date.in_(dates))
        )
        return list(result.scalars().all())

    async def logs_for_user(self, user_id: uuid.UUID) -> list[FocusLog]:
        result = await self.db.execute(
            select(FocusLog).where(FocusLog.user_id == user_id).order_by(FocusLog.log_date)
        )
        return list(result.scalars().all())

    async def get_log(self, user_focus_id: uuid.UUID, log_date: date) -> FocusLog | None:
        result = await self.db.execute(
            select(FocusLog).where(FocusLog.user_focus_id == user_focus_id, FocusLog.log_date == log_date)
        )
        return result.scalar_one_or_none()

    async def add_log(self, log: FocusLog) -> FocusLog:
        self.db.add(log)
        await self.db.flush()
        return log

    async def delete_log(self, log: FocusLog) -> None:
        await self.db.delete(log)

    async def upsert_daily_score(
        self, user_id: uuid.UUID, score_date: date, momentum: int | None, breakdown: dict
    ) -> DailyScore:
        result = await self.db.execute(
            select(DailyScore).where(DailyScore.user_id == user_id, DailyScore.score_date == score_date)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = DailyScore(user_id=user_id, score_date=score_date, momentum=momentum, breakdown=breakdown)
            self.db.add(row)
        else:
            row.momentum = momentum
            row.breakdown = breakdown
        await self.db.flush()
        return row

    async def upsert_area_score(
        self,
        user_id: uuid.UUID,
        user_area_id: uuid.UUID,
        score_date: date,
        score: int,
        breakdown: dict,
    ) -> AreaScore:
        result = await self.db.execute(
            select(AreaScore).where(AreaScore.user_area_id == user_area_id, AreaScore.score_date == score_date)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = AreaScore(
                user_id=user_id,
                user_area_id=user_area_id,
                score_date=score_date,
                score=score,
                breakdown=breakdown,
            )
            self.db.add(row)
        else:
            row.score = score
            row.breakdown = breakdown
        await self.db.flush()
        return row

    async def delete_area_score(self, user_area_id: uuid.UUID, score_date: date) -> None:
        await self.db.execute(
            delete(AreaScore).where(AreaScore.user_area_id == user_area_id, AreaScore.score_date == score_date)
        )
