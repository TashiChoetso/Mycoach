"""Initial schema.

Revision ID: 001_initial
Revises:
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("locale", sa.String(16), nullable=False, server_default="en"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("theme", sa.String(32), nullable=False, server_default="system"),
        sa.Column("week_starts_on", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("scoring_weights", postgresql.JSONB(), nullable=False),
        sa.Column("dashboard_sections", postgresql.JSONB(), nullable=False),
        sa.Column("quiet_hours_start", sa.Time()),
        sa.Column("quiet_hours_end", sa.Time()),
        sa.Column("notification_types", postgresql.JSONB(), nullable=False),
        sa.Column("reminder_time", sa.Time()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table(
        "areas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("icon", sa.String(64)),
        sa.Column("color", sa.String(32)),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("owner_user_id", "name", name="uq_custom_area_name"),
    )
    op.create_table(
        "user_areas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("area_id", sa.Uuid(), sa.ForeignKey("areas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("custom_name", sa.String(120)),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("dashboard_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "area_id", name="uq_user_area"),
    )
    op.create_index("ix_user_areas_user_id", "user_areas", ["user_id"])
    op.create_table(
        "user_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entity_type", sa.String(64)),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("request_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_events_user_id", "user_events", ["user_id"])
    op.create_index("ix_user_events_event_type", "user_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("user_events")
    op.drop_table("user_areas")
    op.drop_table("areas")
    op.drop_table("refresh_tokens")
    op.drop_table("user_preferences")
    op.drop_table("users")
