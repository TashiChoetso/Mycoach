from fastapi import APIRouter, Response

from app.core.deps import CurrentUser, DbSession
from app.schemas import DeleteAccountRequest, PreferencesUpdate, PriorityUpdate, UserOut, UserUpdate
from app.services.user import UserService

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser, db: DbSession) -> UserOut:
    return await UserService(db).me(user)


@router.patch("/me", response_model=UserOut)
async def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession) -> UserOut:
    return await UserService(db).update(user, payload)


@router.patch("/me/preferences", response_model=UserOut)
async def update_preferences(payload: PreferencesUpdate, user: CurrentUser, db: DbSession) -> UserOut:
    return await UserService(db).update_preferences(user, payload)


@router.put("/me/priority")
async def set_priority(payload: PriorityUpdate, user: CurrentUser, db: DbSession) -> dict:
    return await UserService(db).set_priority(user, payload)


@router.post("/me/onboarding/complete", response_model=UserOut)
async def complete_onboarding(user: CurrentUser, db: DbSession) -> UserOut:
    return await UserService(db).complete_onboarding(user)


@router.get("/me/export")
async def export_me(user: CurrentUser, db: DbSession) -> dict:
    return await UserService(db).export(user)


@router.delete("/me", status_code=204)
async def delete_me(payload: DeleteAccountRequest, user: CurrentUser, db: DbSession, response: Response) -> None:
    await UserService(db).delete_account(user, payload.password)
    response.delete_cookie("refresh_token", path="/api/v1/auth")
