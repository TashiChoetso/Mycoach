"""Focus catalog and daily logs.

Revision ID: 002_focuses
Revises: 001_initial
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_focuses"
down_revision: str | None = "001_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "focuses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("prompt", sa.Text()),
        sa.Column("kind", sa.String(16), nullable=False, server_default="check"),
        sa.Column("target_value", sa.Numeric(14, 2)),
        sa.Column("unit", sa.String(32)),
        sa.Column("area_id", sa.Uuid(), sa.ForeignKey("areas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_focuses_area_id", "focuses", ["area_id"])
    op.create_table(
        "user_focuses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_area_id", sa.Uuid(), sa.ForeignKey("user_areas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("focus_id", sa.Uuid(), sa.ForeignKey("focuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("custom_name", sa.String(120)),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "focus_id", name="uq_user_focus"),
    )
    op.create_index("ix_user_focuses_user_id", "user_focuses", ["user_id"])
    op.create_index("ix_user_focuses_user_area_id", "user_focuses", ["user_area_id"])
    op.create_table(
        "focus_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_focus_id", sa.Uuid(), sa.ForeignKey("user_focuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("value", sa.Numeric(14, 2)),
        sa.Column("note", sa.Text()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_focus_id", "log_date", name="uq_focus_log_date"),
    )
    op.create_index("ix_focus_logs_user_id", "focus_logs", ["user_id"])
    op.create_index("ix_focus_logs_log_date", "focus_logs", ["log_date"])


def downgrade() -> None:
    op.drop_table("focus_logs")
    op.drop_table("user_focuses")
    op.drop_table("focuses")
