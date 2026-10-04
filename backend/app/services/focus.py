from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalog import AREA_TONES
from app.core.config import get_settings
from app.core.exceptions import InvalidInput, NotFound
from app.models.area import UserArea
from app.models.focus import Focus, FocusLog, UserFocus
from app.models.user import User
from app.repositories.area import AreaRepository
from app.repositories.event import EventRepository
from app.repositories.focus import FocusRepository
from app.scoring.momentum import (
    completion_rate,
    daterange,
    dates_back,
    score_area,
    score_focus,
    score_momentum,
    week_start,
)
from app.services.area import display_name


def local_today(user: User) -> date:
    try:
        return datetime.now(ZoneInfo(user.timezone)).date()
    except Exception:
        return datetime.now(ZoneInfo("UTC")).date()


def assert_loggable_date(user: User, log_date: date) -> None:
    today = local_today(user)
    if log_date > today:
        raise InvalidInput("You cannot log practices in the future")
    max_past = get_settings().log_date_max_past_days
    if log_date < today - timedelta(days=max_past):
        raise InvalidInput(f"You can only log practices from the last {max_past} days")


def area_tone(slug: str | None) -> str:
    if not slug:
        return "clay"
    return AREA_TONES.get(slug, "clay")


def focus_name(user_focus: UserFocus) -> str:
    return user_focus.custom_name or user_focus.focus.name


def _target(focus: Focus) -> float | None:
    if focus.target_value is None:
        return None
    return float(focus.target_value)


class FocusService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.areas = AreaRepository(db)
        self.focuses = FocusRepository(db)
        self.events = EventRepository(db)

    async def ensure_for_user(self, user: User) -> None:
        selected = await self.areas.list_user_areas(user.id)
        changed = False
        for user_area in selected:
            if await self._ensure_user_area(user, user_area):
                changed = True
        if changed:
            await self.db.commit()

    async def ensure_for_user_area(self, user: User, user_area: UserArea) -> None:
        if await self._ensure_user_area(user, user_area):
            await self.db.flush()

    async def _ensure_user_area(self, _user: User, _user_area: UserArea) -> bool:
        return False

    async def create(self, user: User, payload) -> dict:
        user_area = await self.areas.get_user_area(user.id, uuid.UUID(payload.user_area_id))
        if user_area is None:
            raise NotFound("Unknown area")
        await self.ensure_for_user_area(user, user_area)
        existing = await self.focuses.list_user_focuses(user.id, user_area.id)
        kind = payload.kind or "check"
        if kind not in {"check", "count"}:
            raise InvalidInput("kind must be check or count")
        if kind == "count" and not payload.target_value:
            raise InvalidInput("Count practices need a target, like 8 glasses or 60 minutes")
        focus = await self.focuses.add_focus(
            Focus(
                name=payload.name.strip(),
                prompt=(payload.prompt or "").strip() or None,
                kind=kind,
                target_value=payload.target_value,
                unit=payload.unit,
                area_id=user_area.area_id,
                is_system=False,
                owner_user_id=user.id,
                sort_order=len(existing),
            )
        )
        user_focus = await self.focuses.add_user_focus(
            UserFocus(
                user_id=user.id,
                user_area_id=user_area.id,
                focus_id=focus.id,
                sort_order=len(existing),
            )
        )
        await self.events.emit(
            user_id=user.id,
            event_type="FOCUS_CREATED",
            entity_type="focus",
            entity_id=focus.id,
            metadata={"name": focus.name, "user_area_id": str(user_area.id)},
        )
        await self.db.commit()
        user_focus = await self.focuses.get_user_focus(user.id, user_focus.id)
        assert user_focus is not None
        return self._serialize_focus(user_focus, log=None)

    async def update(self, user: User, user_focus_id: uuid.UUID, payload) -> dict:
        user_focus = await self.focuses.get_user_focus(user.id, user_focus_id)
        if user_focus is None:
            raise NotFound()
        if payload.custom_name is not None:
            user_focus.custom_name = payload.custom_name.strip()
        if payload.is_enabled is not None:
            user_focus.is_enabled = payload.is_enabled
        if payload.sort_order is not None:
            user_focus.sort_order = payload.sort_order
        await self.db.commit()
        user_focus = await self.focuses.get_user_focus(user.id, user_focus_id)
        assert user_focus is not None
        today = local_today(user)
        log = await self.focuses.get_log(user_focus.id, today)
        return self._serialize_focus(user_focus, log)

    async def delete(self, user: User, user_focus_id: uuid.UUID) -> None:
        user_focus = await self.focuses.get_user_focus(user.id, user_focus_id)
        if user_focus is None:
            raise NotFound()
        if user_focus.focus.is_system:
            user_focus.is_enabled = False
        else:
            await self.focuses.delete_user_focus(user_focus)
        await self.db.commit()

    async def complete(self, user: User, user_focus_id: uuid.UUID, payload) -> dict:
        user_focus = await self.focuses.get_user_focus(user.id, user_focus_id)
        if user_focus is None:
            raise NotFound()
        log_date = payload.date or local_today(user)
        assert_loggable_date(user, log_date)
        value = payload.value
        if user_focus.focus.kind == "count":
            if value is None:
                value = _target(user_focus.focus) or 1
            if value < 0:
                raise InvalidInput("Value cannot be negative")
        log = await self._write_log(
            user, user_focus, log_date, status="completed", value=value, note=payload.note
        )
        await self.events.emit(
            user_id=user.id,
            event_type="FOCUS_COMPLETED",
            entity_type="focus",
            entity_id=user_focus.focus_id,
            metadata={"date": log_date.isoformat(), "value": float(log.value) if log.value is not None else None},
        )
        board = await self.compute_board(user, log_date)
        await self.db.commit()
        return {"focus": self._serialize_focus(user_focus, log), "board": board}

    async def skip(self, user: User, user_focus_id: uuid.UUID, payload) -> dict:
        user_focus = await self.focuses.get_user_focus(user.id, user_focus_id)
        if user_focus is None:
            raise NotFound()
        log_date = payload.date or local_today(user)
        assert_loggable_date(user, log_date)
        log = await self._write_log(user, user_focus, log_date, status="skipped", value=None, note=payload.note)
        await self.events.emit(
            user_id=user.id,
            event_type="FOCUS_SKIPPED",
            entity_type="focus",
            entity_id=user_focus.focus_id,
            metadata={"date": log_date.isoformat()},
        )
        board = await self.compute_board(user, log_date)
        await self.db.commit()
        return {"focus": self._serialize_focus(user_focus, log), "board": board}

    async def undo(self, user: User, user_focus_id: uuid.UUID, payload) -> dict:
        user_focus = await self.focuses.get_user_focus(user.id, user_focus_id)
        if user_focus is None:
            raise NotFound()
        log_date = payload.date or local_today(user)
        assert_loggable_date(user, log_date)
        log = await self.focuses.get_log(user_focus.id, log_date)
        if log:
            await self.focuses.delete_log(log)
        board = await self.compute_board(user, log_date)
        await self.db.commit()
        return {"focus": self._serialize_focus(user_focus, None), "board": board}

    async def area_board(self, user: User, user_area_id: uuid.UUID) -> dict:
        await self.ensure_for_user(user)
        user_area = await self.areas.get_user_area(user.id, user_area_id)
        if user_area is None:
            raise NotFound()
        today = local_today(user)
        board = await self.compute_board(user, today)
        await self.db.commit()
        match = next((item for item in board["areas"] if item["id"] == str(user_area_id)), None)
        if match is None:
            raise NotFound()
        return {
            "area": match,
            "week": board["week"],
            "week_days": board.get("week_days") or [],
            "momentum": board["momentum"],
            "date": today.isoformat(),
        }

    async def compute_board(self, user: User, today: date) -> dict:
        await self.ensure_for_user(user)
        selected = [item for item in await self.areas.list_user_areas(user.id) if item.is_enabled]
        focuses = [item for item in await self.focuses.list_user_focuses(user.id) if item.is_enabled]
        week_starts_on = 1
        if user.preferences and user.preferences.week_starts_on is not None:
            week_starts_on = user.preferences.week_starts_on
        calendar_week = daterange(week_start(today, week_starts_on), week_start(today, week_starts_on) + timedelta(days=6))
        history = dates_back(today, 7)
        needed = sorted(set(calendar_week + history))
        logs = await self.focuses.logs_for_dates(user.id, needed)
        log_map = {(item.user_focus_id, item.log_date): item for item in logs}

        areas_out: list[dict] = []
        area_scores: list[int] = []
        due = completed = skipped = 0
        by_area: dict[uuid.UUID, list[UserFocus]] = {}
        for item in focuses:
            by_area.setdefault(item.user_area_id, []).append(item)

        for user_area in selected:
            rows: list[dict] = []
            scores: list[int | None] = []
            area_due = area_done = 0
            for user_focus in by_area.get(user_area.id, []):
                log = log_map.get((user_focus.id, today))
                row = self._serialize_focus(user_focus, log, log_map, calendar_week)
                rows.append(row)
                scores.append(row["score"])
                due += 1
                area_due += 1
                if row["status"] == "completed":
                    completed += 1
                    area_done += 1
                elif row["status"] == "skipped":
                    skipped += 1
            area_score = score_area(scores)
            if area_score is not None:
                area_scores.append(area_score)
                await self.focuses.upsert_area_score(
                    user.id,
                    user_area.id,
                    today,
                    area_score,
                    {"completed": area_done, "due": area_due},
                )
            else:
                await self.focuses.delete_area_score(user_area.id, today)
            areas_out.append(
                {
                    "id": str(user_area.id),
                    "area_id": str(user_area.area_id),
                    "name": display_name(user_area),
                    "slug": user_area.area.slug,
                    "tone": area_tone(user_area.area.slug),
                    "icon": user_area.area.icon,
                    "score": area_score,
                    "completed": area_done,
                    "due": area_due,
                    "focuses": rows,
                }
            )

        day_rates: list[float] = []
        week: list[dict] = []
        for day in history:
            day_completed = day_due = day_skipped = 0
            day_scores: list[int | None] = []
            for user_focus in focuses:
                log = log_map.get((user_focus.id, day))
                day_due += 1
                status = log.status if log else "open"
                if status == "completed":
                    day_completed += 1
                elif status == "skipped":
                    day_skipped += 1
                day_scores.append(
                    score_focus(
                        kind=user_focus.focus.kind,
                        target_value=user_focus.focus.target_value,
                        log_status=log.status if log else None,
                        log_value=log.value if log else None,
                    )
                )
            rate = completion_rate(day_completed, day_due, day_skipped)
            if rate is not None:
                day_rates.append(rate)
            day_area = score_area(day_scores)
            week.append(
                {
                    "date": day.isoformat(),
                    "score": day_area,
                    "completed": day_completed,
                    "due": day_due,
                }
            )

        seven = sum(day_rates) / len(day_rates) if day_rates else None
        rest_day = due == 0 or due == skipped
        momentum = None if rest_day else score_momentum(area_scores, seven)
        await self.focuses.upsert_daily_score(
            user.id,
            today,
            momentum,
            {"completed": completed, "due": due, "skipped": skipped, "seven_day_rate": seven},
        )

        remaining = max(0, due - skipped - completed)
        if rest_day and due == 0:
            label = "Nothing planned yet"
        elif rest_day:
            label = "Rest day"
        elif completed == 0:
            label = f"{due - skipped} practices on the map"
        else:
            label = f"{completed} of {due - skipped} done"

        return {
            "date": today.isoformat(),
            "momentum": {
                "score": momentum,
                "max": 100,
                "rest_day": rest_day,
                "label": label,
                "completed": completed,
                "due": due - skipped,
                "remaining": remaining,
            },
            "week": week,
            "week_days": [
                {"date": day.isoformat(), "weekday": day.strftime("%a"), "is_today": day == today, "is_future": day > today}
                for day in calendar_week
            ],
            "areas": areas_out,
            "seven_day_rate": seven,
        }

    async def progress(self, user: User, *, span: str, offset: int = 0, day: date | None = None) -> dict:
        if span not in {"day", "week", "month"}:
            raise InvalidInput("range must be day, week, or month")
        await self.ensure_for_user(user)
        today = local_today(user)
        week_starts_on = 1
        if user.preferences and user.preferences.week_starts_on is not None:
            week_starts_on = user.preferences.week_starts_on
        selected = [item for item in await self.areas.list_user_areas(user.id) if item.is_enabled]
        focuses = [item for item in await self.focuses.list_user_focuses(user.id) if item.is_enabled]
        by_area: dict[uuid.UUID, list[UserFocus]] = {}
        for item in focuses:
            by_area.setdefault(item.user_area_id, []).append(item)

        this_week = week_start(today, week_starts_on)
        if span == "day":
            anchor = day or today
            start = end = anchor
            series_start = anchor - timedelta(days=13)
            label = "Today" if anchor == today else anchor.strftime("%d %b")
        elif span == "week":
            start = this_week - timedelta(days=7 * max(0, offset))
            end = start + timedelta(days=6)
            series_start = start
            label = "This week" if offset == 0 else ("Last week" if offset == 1 else f"Week of {start.strftime('%d %b')}")
            anchor = min(today, end)
        else:
            month_cursor = date(today.year, today.month, 1)
            for _ in range(max(0, offset)):
                month_cursor = (month_cursor - timedelta(days=1)).replace(day=1)
            start = month_cursor
            if start.month == 12:
                end = date(start.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(start.year, start.month + 1, 1) - timedelta(days=1)
            series_start = start
            label = "This month" if offset == 0 else start.strftime("%B %Y")
            anchor = min(today, end)

        lookback_start = min(series_start, start, this_week - timedelta(days=7 * 7), today - timedelta(days=21))
        lookback_end = max(end, today)
        logs = await self.focuses.logs_for_dates(user.id, daterange(lookback_start, lookback_end))
        log_map = {(item.user_focus_id, item.log_date): item for item in logs}

        series = [
            self._day_rollup(focuses, log_map, item, today)
            for item in daterange(series_start, end if span != "day" else today)
        ]
        days = [
            self._day_detail(selected, by_area, log_map, item, today)
            for item in daterange(start, end)
        ]

        weeks = []
        for week_offset in range(0, 8):
            w_start = this_week - timedelta(days=7 * week_offset)
            w_end = w_start + timedelta(days=6)
            rollups = [self._day_rollup(focuses, log_map, item, today) for item in daterange(w_start, w_end)]
            scored = [row["score"] for row in rollups if row["score"] is not None]
            weeks.append(
                {
                    "offset": week_offset,
                    "label": "This week" if week_offset == 0 else ("Last week" if week_offset == 1 else w_start.strftime("%d %b")),
                    "start": w_start.isoformat(),
                    "end": w_end.isoformat(),
                    "score": round(sum(scored) / len(scored)) if scored else None,
                    "completed": sum(row["completed"] for row in rollups),
                    "due": sum(row["due"] for row in rollups),
                }
            )

        calendar: list[dict] = []
        if span == "month":
            grid_start = week_start(start, week_starts_on)
            grid_end = week_start(end, week_starts_on) + timedelta(days=6)
            for item in daterange(grid_start, grid_end):
                rollup = self._day_rollup(focuses, log_map, item, today)
                calendar.append({**rollup, "in_month": item.month == start.month})

        window = [row for row in series if start.isoformat() <= row["date"] <= end.isoformat()]
        scored = [row["score"] for row in window if row["score"] is not None]
        completed = sum(row["completed"] for row in window)
        due = sum(row["due"] for row in window)
        best = max(window, key=lambda row: row["score"] or -1, default=None)
        streak = 0
        cursor = today
        while True:
            rollup = self._day_rollup(focuses, log_map, cursor, today)
            if rollup["completed"] <= 0:
                break
            streak += 1
            cursor -= timedelta(days=1)

        area_stats: list[dict] = []
        for user_area in selected:
            area_scores: list[int] = []
            area_done = area_due = 0
            for item in daterange(start, min(end, today)):
                detail = next((block for block in days if block["date"] == item.isoformat()), None)
                if not detail:
                    continue
                match = next((block for block in detail["areas"] if block["id"] == str(user_area.id)), None)
                if not match:
                    continue
                area_done += match["completed"]
                area_due += match["due"]
                if match["score"] is not None:
                    area_scores.append(match["score"])
            area_stats.append(
                {
                    "id": str(user_area.id),
                    "name": display_name(user_area),
                    "slug": user_area.area.slug,
                    "tone": area_tone(user_area.area.slug),
                    "score": round(sum(area_scores) / len(area_scores)) if area_scores else None,
                    "completed": area_done,
                    "due": area_due,
                }
            )

        return {
            "range": span,
            "offset": offset,
            "anchor": anchor.isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "label": label,
            "today": today.isoformat(),
            "summary": {
                "score": round(sum(scored) / len(scored)) if scored else None,
                "completed": completed,
                "due": due,
                "days_active": sum(1 for row in window if row["completed"] > 0),
                "streak": streak,
                "best": {"date": best["date"], "score": best["score"]} if best and best["score"] is not None else None,
            },
            "series": series,
            "weeks": weeks,
            "days": days,
            "calendar": calendar,
            "areas": area_stats,
        }

    def _day_rollup(self, focuses: list[UserFocus], log_map: dict, day: date, today: date) -> dict:
        completed = due = skipped = 0
        scores: list[int | None] = []
        for user_focus in focuses:
            log = log_map.get((user_focus.id, day))
            due += 1
            status = log.status if log else "open"
            if status == "completed":
                completed += 1
            elif status == "skipped":
                skipped += 1
            scores.append(
                score_focus(
                    kind=user_focus.focus.kind,
                    target_value=user_focus.focus.target_value,
                    log_status=log.status if log else None,
                    log_value=log.value if log else None,
                )
            )
        rest = due == 0 or due == skipped or day > today
        score = None if rest or day > today else score_area(scores)
        return {
            "date": day.isoformat(),
            "weekday": day.strftime("%a"),
            "score": score,
            "completed": completed,
            "due": max(0, due - skipped),
            "is_today": day == today,
            "is_future": day > today,
        }

    def _day_detail(
        self,
        selected: list,
        by_area: dict[uuid.UUID, list[UserFocus]],
        log_map: dict,
        day: date,
        today: date,
    ) -> dict:
        rollup = self._day_rollup([item for rows in by_area.values() for item in rows], log_map, day, today)
        areas_out = []
        for user_area in selected:
            rows = []
            scores: list[int | None] = []
            done = due = 0
            for user_focus in by_area.get(user_area.id, []):
                log = log_map.get((user_focus.id, day))
                row = self._serialize_focus(user_focus, log)
                if day > today and row["status"] == "open":
                    row = {**row, "status": "upcoming"}
                rows.append(row)
                scores.append(row["score"] if row["status"] != "upcoming" else None)
                due += 1
                if row["status"] == "completed":
                    done += 1
            areas_out.append(
                {
                    "id": str(user_area.id),
                    "name": display_name(user_area),
                    "tone": area_tone(user_area.area.slug),
                    "score": None if day > today else score_area(scores),
                    "completed": done,
                    "due": due,
                    "focuses": rows,
                }
            )
        return {**rollup, "areas": areas_out}

    async def _write_log(
        self,
        user: User,
        user_focus: UserFocus,
        log_date: date,
        *,
        status: str,
        value: float | None,
        note: str | None,
    ) -> FocusLog:
        log = await self.focuses.get_log(user_focus.id, log_date)
        now = datetime.now(UTC)
        if log is None:
            log = await self.focuses.add_log(
                FocusLog(
                    user_id=user.id,
                    user_focus_id=user_focus.id,
                    log_date=log_date,
                    status=status,
                    value=value,
                    note=note,
                    completed_at=now if status == "completed" else None,
                )
            )
        else:
            log.status = status
            log.value = value
            log.note = note
            log.completed_at = now if status == "completed" else None
        return log

    def _serialize_focus(
        self,
        user_focus: UserFocus,
        log: FocusLog | None,
        log_map: dict | None = None,
        mark_dates: list[date] | None = None,
    ) -> dict:
        status = log.status if log else "open"
        value = float(log.value) if log and log.value is not None else None
        score = score_focus(
            kind=user_focus.focus.kind,
            target_value=user_focus.focus.target_value,
            log_status=log.status if log else None,
            log_value=log.value if log else None,
        )
        marks = []
        if log_map is not None and mark_dates:
            for day in mark_dates:
                entry = log_map.get((user_focus.id, day))
                marks.append(
                    {
                        "date": day.isoformat(),
                        "weekday": day.strftime("%a"),
                        "status": entry.status if entry else "open",
                    }
                )
        return {
            "id": str(user_focus.id),
            "focus_id": str(user_focus.focus_id),
            "user_area_id": str(user_focus.user_area_id),
            "name": focus_name(user_focus),
            "prompt": user_focus.focus.prompt,
            "kind": user_focus.focus.kind,
            "target_value": _target(user_focus.focus),
            "unit": user_focus.focus.unit,
            "is_system": user_focus.focus.is_system,
            "is_enabled": user_focus.is_enabled,
            "status": status,
            "value": value,
            "score": score,
            "marks": marks,
        }
