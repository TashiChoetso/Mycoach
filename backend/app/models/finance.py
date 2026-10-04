from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class ExpenseCategory(TimestampMixin, Base):
    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("expense_categories.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(64))
    is_system: Mapped[bool] = mapped_column(default=True)


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("expense_categories.id", ondelete="SET NULL")
    )
    user_area_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="SET NULL")
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="expense")
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    payment_method: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)


class Budget(TimestampMixin, Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("expense_categories.id", ondelete="SET NULL")
    )
    user_area_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="SET NULL")
    )
    period: Mapped[str] = mapped_column(String(16), nullable=False, default="monthly")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
