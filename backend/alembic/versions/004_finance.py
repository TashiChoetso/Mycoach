"""Expense categories, expenses, and budgets.

Revision ID: 004_finance
Revises: 003_live_tables
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_finance"
down_revision: str | None = "003_live_tables"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing = _tables()

    if "expense_categories" not in existing:
        op.create_table(
            "expense_categories",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE")),
            sa.Column("parent_id", sa.Uuid()),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("slug", sa.String(64)),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["parent_id"], ["expense_categories.id"], ondelete="SET NULL"),
        )

    if "expenses" not in existing:
        op.create_table(
            "expenses",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column(
                "category_id",
                sa.Uuid(),
                sa.ForeignKey("expense_categories.id", ondelete="SET NULL"),
            ),
            sa.Column("user_area_id", sa.Uuid(), sa.ForeignKey("user_areas.id", ondelete="SET NULL")),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
            sa.Column("type", sa.String(16), nullable=False, server_default="expense"),
            sa.Column("occurred_on", sa.Date(), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("payment_method", sa.String(32)),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_expenses_user_id", "expenses", ["user_id"])
        op.create_index("ix_expenses_occurred_on", "expenses", ["occurred_on"])

    if "budgets" not in existing:
        op.create_table(
            "budgets",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column(
                "category_id",
                sa.Uuid(),
                sa.ForeignKey("expense_categories.id", ondelete="SET NULL"),
            ),
            sa.Column("user_area_id", sa.Uuid(), sa.ForeignKey("user_areas.id", ondelete="SET NULL")),
            sa.Column("period", sa.String(16), nullable=False, server_default="monthly"),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_budgets_user_id", "budgets", ["user_id"])


def downgrade() -> None:
    existing = _tables()
    if "budgets" in existing:
        op.drop_table("budgets")
    if "expenses" in existing:
        op.drop_table("expenses")
    if "expense_categories" in existing:
        op.drop_table("expense_categories")
