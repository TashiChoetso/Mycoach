from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Area(TimestampMixin, Base):
    __tablename__ = "areas"
    __table_args__ = (UniqueConstraint("owner_user_id", "name", name="uq_custom_area_name"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(64))
    color: Mapped[str | None] = mapped_column(String(32))
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserArea(TimestampMixin, Base):
    __tablename__ = "user_areas"
    __table_args__ = (UniqueConstraint("user_id", "area_id", name="uq_user_area"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    area_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("areas.id", ondelete="CASCADE"), nullable=False
    )
    custom_name: Mapped[str | None] = mapped_column(String(120))
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    dashboard_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship(back_populates="areas")
    area: Mapped[Area] = relationship()
