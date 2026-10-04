from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas import TodayDashboard
from app.scoring.weights import FINANCE_SLUG
from app.services.focus import FocusService, local_today
from app.services.user import UserService


QUOTES = [
    "Small progress every day becomes big change over time.",
    "You do not have to do everything today. You only have to begin.",
    "Consistency is quieter than motivation, and more reliable.",
    "A gentle restart still counts as showing up.",
]


def _period(now: datetime) -> str:
    hour = now.hour
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def _greeting_word(period: str) -> str:
    return {"morning": "Good morning", "afternoon": "Good afternoon", "evening": "Good evening"}[period]


def _coach(first: str, board: dict) -> str:
    if not board["areas"]:
        return (
            f"Good to meet you, {first}. Choose the parts of life you want to change "
            "and we'll score the small daily practices."
        )
    momentum = board["momentum"]
    remaining = momentum.get("remaining") or 0
    score = momentum.get("score")
    if momentum.get("rest_day") and (momentum.get("due") or 0) == 0:
        return f"Your map is ready, {first}. Write today’s priority, then add what you’ll actually do under each area."
    if score in (None, 0):
        return f"Start tiny, {first}. One honest check under an area you care about."
    if remaining == 0:
        return f"That's a complete day, {first}. Protect it. Don't add more just to chase the number."
    if score < 50:
        noun = "practice" if remaining == 1 else "practices"
        return f"Good start, {first}. {remaining} {noun} still open. Pick the one you'd respect tomorrow."
    return f"You're stacking a real day, {first}. Finish the next one clean, then stop."


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.focuses = FocusService(db)

    async def today(self, user: User) -> TodayDashboard:
        try:
            now = datetime.now(ZoneInfo(user.timezone))
        except Exception:
            now = datetime.now(ZoneInfo("UTC"))
        period = _period(now)
        today = local_today(user)
        board = await self.focuses.compute_board(user, today)
        await self.db.commit()
        priorities = await UserService(self.db).priorities(user)
        finance_enabled = any(item.get("slug") == FINANCE_SLUG for item in board["areas"])
        quote = QUOTES[now.toordinal() % len(QUOTES)]
        first = user.display_name.split(" ")[0]
        checkins = []
        for area in board["areas"]:
            checkins.extend(area.get("focuses") or [])
        return TodayDashboard(
            greeting={
                "name": first,
                "period": period,
                "hello": f"{_greeting_word(period)}, {first}",
                "quote": quote,
            },
            momentum=board["momentum"],
            week=board["week"],
            week_days=board.get("week_days") or [],
            tasks={"items": checkins, "completed": board["momentum"]["completed"], "total": board["momentum"]["due"]},
            habits={"items": [], "completed": 0, "due": 0},
            finance=None
            if not finance_enabled
            else {"spent_today": 0, "daily_budget": None, "remaining": None, "categories": []},
            areas=board["areas"],
            coach={"message": _coach(first, board), "cta": None},
            date=board["date"],
            priorities=priorities,
        )
