from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class Goal(TimestampMixin, Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_area_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    current_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    unit: Mapped[str | None] = mapped_column(String(32))
    start_date: Mapped[date | None] = mapped_column(Date)
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)


class GoalMilestone(TimestampMixin, Base):
    __tablename__ = "goal_milestones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Habit(TimestampMixin, Base):
    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_area_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    frequency_type: Mapped[str] = mapped_column(String(32), nullable=False, default="daily")
    frequency_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    target_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    target_unit: Mapped[str | None] = mapped_column(String(32))
    reminder_time: Mapped[time | None] = mapped_column(Time)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class HabitLog(TimestampMixin, Base):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    habit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    note: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_area_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="SET NULL")
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"))
    habit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("habits.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    recurrence_type: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    recurrence_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="todo")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    skipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskCompletion(TimestampMixin, Base):
    __tablename__ = "task_completions"
    __table_args__ = (UniqueConstraint("task_id", "occurrence_date", name="uq_task_occurrence"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    occurrence_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
