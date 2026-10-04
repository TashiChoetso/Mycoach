from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.exceptions import Unauthorized
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized()
    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = uuid.UUID(payload["sub"])
    except Exception as exc:
        raise Unauthorized() from exc
    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise Unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
RequestId = Annotated[str | None, Header(alias="X-Request-ID")]
