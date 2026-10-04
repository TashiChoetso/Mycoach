import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas import FocusCreate, FocusLogRequest, FocusUpdate
from app.services.focus import FocusService

router = APIRouter(prefix="/focuses", tags=["focuses"])


@router.post("", status_code=201)
async def create_focus(payload: FocusCreate, user: CurrentUser, db: DbSession) -> dict:
    return await FocusService(db).create(user, payload)


@router.patch("/{user_focus_id}")
async def update_focus(user_focus_id: uuid.UUID, payload: FocusUpdate, user: CurrentUser, db: DbSession) -> dict:
    return await FocusService(db).update(user, user_focus_id, payload)


@router.delete("/{user_focus_id}", status_code=204)
async def delete_focus(user_focus_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    await FocusService(db).delete(user, user_focus_id)


@router.post("/{user_focus_id}/complete")
async def complete_focus(user_focus_id: uuid.UUID, payload: FocusLogRequest, user: CurrentUser, db: DbSession) -> dict:
    return await FocusService(db).complete(user, user_focus_id, payload)


@router.post("/{user_focus_id}/skip")
async def skip_focus(user_focus_id: uuid.UUID, payload: FocusLogRequest, user: CurrentUser, db: DbSession) -> dict:
    return await FocusService(db).skip(user, user_focus_id, payload)


@router.post("/{user_focus_id}/undo")
async def undo_focus(user_focus_id: uuid.UUID, payload: FocusLogRequest, user: CurrentUser, db: DbSession) -> dict:
    return await FocusService(db).undo(user, user_focus_id, payload)
