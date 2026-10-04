from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class DailyScore(TimestampMixin, Base):
    __tablename__ = "daily_scores"
    __table_args__ = (UniqueConstraint("user_id", "score_date", name="uq_daily_score"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    momentum: Mapped[int | None] = mapped_column(Integer)
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AreaScore(TimestampMixin, Base):
    __tablename__ = "area_scores"
    __table_args__ = (UniqueConstraint("user_area_id", "score_date", name="uq_area_score"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_area_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="CASCADE"), nullable=False
    )
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    __table_args__ = (UniqueConstraint("user_id", "period_start", name="uq_daily_metrics"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class WeeklyMetric(Base):
    __tablename__ = "weekly_metrics"
    __table_args__ = (UniqueConstraint("user_id", "period_start", name="uq_weekly_metrics"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class MonthlyMetric(Base):
    __tablename__ = "monthly_metrics"
    __table_args__ = (UniqueConstraint("user_id", "period_start", name="uq_monthly_metrics"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CustomMetric(TimestampMixin, Base):
    __tablename__ = "custom_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_area_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("user_areas.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32))
    aggregation: Mapped[str] = mapped_column(String(16), nullable=False, default="sum")


class MetricLog(Base):
    __tablename__ = "metric_logs"
    __table_args__ = (UniqueConstraint("metric_id", "log_date", name="uq_metric_log_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("custom_metrics.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
