from __future__ import annotations

import math
from datetime import date, timedelta


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _num(value: object | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def score_focus(
    *,
    kind: str,
    target_value: object | None,
    log_status: str | None,
    log_value: object | None,
) -> int | None:
    """Score one daily practice. Skipped items are omitted from the average."""
    if log_status == "skipped":
        return None
    if log_status != "completed":
        return 0
    if kind == "count":
        target = _num(target_value)
        if target <= 0:
            return 100
        return clamp_score(100 * _num(log_value) / target)
    return 100


def score_area(focus_scores: list[int | None]) -> int | None:
    active = [item for item in focus_scores if item is not None]
    if not active:
        return None
    return clamp_score(sum(active) / len(active))


def score_momentum(area_scores: list[int], seven_day_rate: float | None = None) -> int:
    if not area_scores:
        return 0
    mean = sum(area_scores) / len(area_scores)
    bonus = math.floor((seven_day_rate or 0) * 5)
    return min(100, round(mean) + bonus)


def completion_rate(completed: int, due: int, skipped: int) -> float | None:
    denom = due - skipped
    if denom <= 0:
        return None
    return completed / denom


def dates_back(today: date, days: int) -> list[date]:
    return [date.fromordinal(today.toordinal() - offset) for offset in range(days - 1, -1, -1)]


def daterange(start: date, end: date) -> list[date]:
    if end < start:
        return []
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def week_start(day: date, week_starts_on: int = 1) -> date:
    """week_starts_on: 0=Sunday … 6=Saturday (user_preferences)."""
    python_start = (week_starts_on - 1) % 7
    return day - timedelta(days=(day.weekday() - python_start) % 7)
