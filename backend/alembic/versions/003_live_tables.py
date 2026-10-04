"""Live tables used by the Phase-1 practice loop.

Revision ID: 003_live_tables
Revises: 002_focuses
Create Date: 2026-03-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_live_tables"
down_revision: str | None = "002_focuses"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing = _tables()

    if "user_priorities" not in existing:
        op.create_table(
            "user_priorities",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("period", sa.String(16), nullable=False),
            sa.Column("period_key", sa.String(16), nullable=False),
            sa.Column("text", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "period", "period_key", name="uq_user_priority"),
        )
        op.create_index("ix_user_priorities_user_id", "user_priorities", ["user_id"])

    if "daily_scores" not in existing:
        op.create_table(
            "daily_scores",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("score_date", sa.Date(), nullable=False),
            sa.Column("momentum", sa.Integer()),
            sa.Column("breakdown", postgresql.JSONB(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "score_date", name="uq_daily_score"),
        )
        op.create_index("ix_daily_scores_user_id", "daily_scores", ["user_id"])

    if "area_scores" not in existing:
        op.create_table(
            "area_scores",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column(
                "user_area_id",
                sa.Uuid(),
                sa.ForeignKey("user_areas.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("score_date", sa.Date(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("breakdown", postgresql.JSONB(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_area_id", "score_date", name="uq_area_score"),
        )
        op.create_index("ix_area_scores_user_id", "area_scores", ["user_id"])

    if "password_reset_tokens" not in existing:
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.Text(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    existing = _tables()
    if "password_reset_tokens" in existing:
        op.drop_table("password_reset_tokens")
    if "area_scores" in existing:
        op.drop_table("area_scores")
    if "daily_scores" in existing:
        op.drop_table("daily_scores")
    if "user_priorities" in existing:
        op.drop_table("user_priorities")
