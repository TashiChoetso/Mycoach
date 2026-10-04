from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas import TodayDashboard
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/today", response_model=TodayDashboard)
async def today(user: CurrentUser, db: DbSession) -> TodayDashboard:
    return await DashboardService(db).today(user)
