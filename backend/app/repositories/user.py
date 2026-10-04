from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import PasswordResetToken, RefreshToken, User, UserPreferences, UserPriority


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.preferences), selectinload(User.areas))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def add_preferences(self, prefs: UserPreferences) -> None:
        self.db.add(prefs)

    async def add_refresh_token(self, token: RefreshToken) -> None:
        self.db.add(token)

    async def get_refresh_token(self, token_id: uuid.UUID) -> RefreshToken | None:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.id == token_id))
        return result.scalar_one_or_none()

    async def revoke_refresh_tokens(self, user_id: uuid.UUID) -> None:
        from datetime import UTC, datetime

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        )
        now = datetime.now(UTC)
        for row in result.scalars().all():
            row.revoked_at = now

    async def add_password_reset(self, token: PasswordResetToken) -> None:
        self.db.add(token)

    async def get_password_reset(self, token_id: uuid.UUID) -> PasswordResetToken | None:
        result = await self.db.execute(select(PasswordResetToken).where(PasswordResetToken.id == token_id))
        return result.scalar_one_or_none()

    async def delete_user(self, user: User) -> None:
        # Use SQL DELETE so Postgres ON DELETE CASCADE runs; ORM relationship
        # teardown otherwise tries to NULL user_preferences.user_id first.
        await self.db.execute(delete(User).where(User.id == user.id))
        self.db.expire_all()

    async def get_priority(self, user_id: uuid.UUID, period: str, period_key: str) -> UserPriority | None:
        result = await self.db.execute(
            select(UserPriority).where(
                UserPriority.user_id == user_id,
                UserPriority.period == period,
                UserPriority.period_key == period_key,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_priority(self, user_id: uuid.UUID, period: str, period_key: str, text: str) -> UserPriority:
        row = await self.get_priority(user_id, period, period_key)
        if row is None:
            row = UserPriority(user_id=user_id, period=period, period_key=period_key, text=text)
            self.db.add(row)
        else:
            row.text = text
        await self.db.flush()
        return row

    async def list_priorities(self, user_id: uuid.UUID) -> list[UserPriority]:
        result = await self.db.execute(select(UserPriority).where(UserPriority.user_id == user_id))
        return list(result.scalars().all())
