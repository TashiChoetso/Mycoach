import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas import AreaCreate, AreaUpdate, AreasResponse, SelectedAreaOut
from app.services.area import AreaService
from app.services.focus import FocusService

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("", response_model=AreasResponse)
async def list_areas(user: CurrentUser, db: DbSession) -> AreasResponse:
    return await AreaService(db).list(user)


@router.post("", response_model=SelectedAreaOut, status_code=201)
async def create_area(payload: AreaCreate, user: CurrentUser, db: DbSession) -> SelectedAreaOut:
    return await AreaService(db).create(user, payload)


@router.get("/{user_area_id}")
async def area_board(user_area_id: uuid.UUID, user: CurrentUser, db: DbSession) -> dict:
    return await FocusService(db).area_board(user, user_area_id)


@router.patch("/{user_area_id}", response_model=SelectedAreaOut)
async def update_area(
    user_area_id: uuid.UUID, payload: AreaUpdate, user: CurrentUser, db: DbSession
) -> SelectedAreaOut:
    return await AreaService(db).update(user, user_area_id, payload)


@router.delete("/{user_area_id}", status_code=204)
async def delete_area(user_area_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    await AreaService(db).delete(user, user_area_id)
