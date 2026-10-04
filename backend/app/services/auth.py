from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalog import DEFAULT_DASHBOARD_SECTIONS, DEFAULT_SCORING_WEIGHTS
from app.core.config import get_settings
from app.core.exceptions import Conflict, InvalidInput, Unauthorized
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from app.models.user import PasswordResetToken, RefreshToken, User, UserPreferences
from app.repositories.event import EventRepository
from app.repositories.user import UserRepository
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.area import serialize_user

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.events = EventRepository(db)

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise Conflict("An account with this email already exists")
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name.strip(),
            timezone=payload.timezone,
        )
        await self.users.create(user)
        await self.users.add_preferences(
            UserPreferences(
                user_id=user.id,
                scoring_weights=DEFAULT_SCORING_WEIGHTS.copy(),
                dashboard_sections=list(DEFAULT_DASHBOARD_SECTIONS),
                notification_types={
                    "morning": True,
                    "habit_reminder": True,
                    "progress": True,
                    "evening": True,
                    "weekly": True,
                },
            )
        )
        tokens = await self._issue_tokens(user)
        await self.events.emit(user_id=user.id, event_type="LOGIN", metadata={"method": "register"})
        await self.db.commit()
        user = await self.users.get_by_id(user.id)
        assert user is not None
        return tokens.model_copy(update={"user": serialize_user(user, [])})

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise Unauthorized("Email or password is incorrect")
        if not user.is_active:
            raise Unauthorized("Email or password is incorrect")
        tokens = await self._issue_tokens(user)
        await self.events.emit(user_id=user.id, event_type="LOGIN", metadata={"method": "password"})
        await self.db.commit()
        full = await self.users.get_by_id(user.id)
        assert full is not None
        from app.repositories.area import AreaRepository

        selected = await AreaRepository(self.db).list_user_areas(full.id)
        return tokens.model_copy(update={"user": serialize_user(full, selected)})

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, "refresh")
            token_id = uuid.UUID(payload["jti"])
            user_id = uuid.UUID(payload["sub"])
        except Exception as exc:
            raise Unauthorized() from exc
        stored = await self.users.get_refresh_token(token_id)
        if (
            stored is None
            or stored.user_id != user_id
            or stored.revoked_at is not None
            or stored.expires_at < datetime.now(UTC)
            or not verify_token_hash(refresh_token, stored.token_hash)
        ):
            raise Unauthorized()
        stored.revoked_at = datetime.now(UTC)
        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise Unauthorized()
        tokens = await self._issue_tokens(user)
        await self.db.commit()
        from app.repositories.area import AreaRepository

        selected = await AreaRepository(self.db).list_user_areas(user.id)
        return tokens.model_copy(update={"user": serialize_user(user, selected)})

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token, "refresh")
            stored = await self.users.get_refresh_token(uuid.UUID(payload["jti"]))
        except Exception:
            return
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            await self.db.commit()

    async def request_password_reset(self, email: str) -> str | None:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active:
            return None
        token_id = uuid.uuid4()
        secret = secrets.token_urlsafe(32)
        await self.users.add_password_reset(
            PasswordResetToken(
                id=token_id,
                user_id=user.id,
                token_hash=hash_token(secret),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        await self.events.emit(user_id=user.id, event_type="PASSWORD_RESET_REQUESTED", metadata={})
        await self.db.commit()
        return f"{token_id}.{secret}"

    async def reset_password(self, token: str, new_password: str) -> None:
        try:
            token_id_str, secret = token.split(".", 1)
            token_id = uuid.UUID(token_id_str)
        except ValueError as exc:
            raise InvalidInput("Reset link is invalid or expired") from exc
        match = await self.users.get_password_reset(token_id)
        if (
            match is None
            or match.used_at is not None
            or match.expires_at < datetime.now(UTC)
            or not verify_token_hash(secret, match.token_hash)
        ):
            raise InvalidInput("Reset link is invalid or expired")
        user = await self.users.get_by_id(match.user_id)
        if user is None or not user.is_active:
            raise InvalidInput("Reset link is invalid or expired")
        user.password_hash = hash_password(new_password)
        match.used_at = datetime.now(UTC)
        await self.users.revoke_refresh_tokens(user.id)
        await self.events.emit(user_id=user.id, event_type="PASSWORD_RESET", metadata={})
        await self.db.commit()

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise Unauthorized("Current password is incorrect")
        if current_password == new_password:
            raise InvalidInput("New password must be different")
        user.password_hash = hash_password(new_password)
        await self.users.revoke_refresh_tokens(user.id)
        await self.events.emit(user_id=user.id, event_type="PASSWORD_CHANGED", metadata={})
        await self.db.commit()

    async def _issue_tokens(self, user: User) -> TokenResponse:
        token_id = uuid.uuid4()
        refresh = create_refresh_token(user.id, token_id)
        access, expires_in = create_access_token(user.id)
        await self.users.add_refresh_token(
            RefreshToken(
                id=token_id,
                user_id=user.id,
                token_hash=hash_token(refresh),
                expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
            )
        )
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=expires_in,
            user=UserOut(
                id=str(user.id),
                email=user.email,
                display_name=user.display_name,
                timezone=user.timezone,
                locale=user.locale,
                currency=user.currency,
                onboarding_completed_at=None,
            ),
        )
