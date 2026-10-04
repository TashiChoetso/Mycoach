from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.area import UserArea


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    preferences: Mapped[UserPreferences] = relationship(back_populates="user", uselist=False)
    areas: Mapped[list[UserArea]] = relationship(back_populates="user")


class UserPreferences(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    theme: Mapped[str] = mapped_column(String(32), nullable=False, default="system")
    week_starts_on: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scoring_weights: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    dashboard_sections: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time)
    notification_types: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reminder_time: Mapped[time | None] = mapped_column(Time)

    user: Mapped[User] = relationship(back_populates="preferences")


class UserPriority(TimestampMixin, Base):
    __tablename__ = "user_priorities"
    __table_args__ = (UniqueConstraint("user_id", "period", "period_key", name="uq_user_priority"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    period_key: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetToken(TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
