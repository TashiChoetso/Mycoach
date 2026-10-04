from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.area import Area, UserArea
    from app.models.user import User


class Focus(TimestampMixin, Base):
    __tablename__ = "focuses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="check")
    target_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    unit: Mapped[str | None] = mapped_column(String(32))
    area_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    area: Mapped[Area] = relationship()


class UserFocus(TimestampMixin, Base):
    __tablename__ = "user_focuses"
    __table_args__ = (UniqueConstraint("user_id", "focus_id", name="uq_user_focus"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_area_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    focus_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("focuses.id", ondelete="CASCADE"), nullable=False
    )
    custom_name: Mapped[str | None] = mapped_column(String(120))
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship()
    user_area: Mapped[UserArea] = relationship()
    focus: Mapped[Focus] = relationship()


class FocusLog(TimestampMixin, Base):
    __tablename__ = "focus_logs"
    __table_args__ = (UniqueConstraint("user_focus_id", "log_date", name="uq_focus_log_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_focus_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_focuses.id", ondelete="CASCADE"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    note: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
