from datetime import date as Date

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.services.focus import FocusService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/progress")
async def progress(
    user: CurrentUser,
    db: DbSession,
    range: str = Query(default="week"),
    offset: int = Query(default=0, ge=0, le=24),
    day: Date | None = None,
) -> dict:
    payload = await FocusService(db).progress(user, span=range, offset=offset, day=day)
    await db.commit()
    return payload
