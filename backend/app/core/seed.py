from __future__ import annotations

import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalog import DEFAULT_AREAS, DEFAULT_FOCUSES
from app.models.area import Area
from app.models.finance import ExpenseCategory
from app.models.focus import Focus

SYSTEM_EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Education",
    "Travel",
    "Subscriptions",
    "Other",
]

logger = logging.getLogger(__name__)


async def seed_catalog(db: AsyncSession) -> None:
    await db.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    existing = set((await db.execute(select(Area.slug).where(Area.is_system.is_(True)))).scalars().all())
    for item in DEFAULT_AREAS:
        if item["slug"] in existing:
            continue
        db.add(
            Area(
                slug=str(item["slug"]),
                name=str(item["name"]),
                icon=str(item["icon"]),
                is_system=True,
                sort_order=int(item["sort_order"]),
            )
        )
    cats = set(
        (await db.execute(select(ExpenseCategory.slug).where(ExpenseCategory.is_system.is_(True)))).scalars().all()
    )
    for name in SYSTEM_EXPENSE_CATEGORIES:
        slug = name.lower()
        if slug in cats:
            continue
        db.add(ExpenseCategory(name=name, slug=slug, is_system=True, user_id=None))
    areas_by_slug = {
        row.slug: row
        for row in (await db.execute(select(Area).where(Area.is_system.is_(True)))).scalars().all()
        if row.slug
    }
    existing_focus = set((await db.execute(select(Focus.slug).where(Focus.is_system.is_(True)))).scalars().all())
    for area_slug, items in DEFAULT_FOCUSES.items():
        area = areas_by_slug.get(area_slug)
        if area is None:
            continue
        for item in items:
            slug = str(item["slug"])
            if slug in existing_focus:
                continue
            target = item.get("target_value")
            db.add(
                Focus(
                    slug=slug,
                    name=str(item["name"]),
                    prompt=str(item.get("prompt") or ""),
                    kind=str(item.get("kind") or "check"),
                    target_value=float(target) if target is not None else None,
                    unit=str(item["unit"]) if item.get("unit") else None,
                    area_id=area.id,
                    is_system=True,
                    sort_order=int(item.get("sort_order") or 0),
                )
            )
    await db.commit()
    logger.info("catalog_seeded", extra={"areas": len(DEFAULT_AREAS), "focuses": len(DEFAULT_FOCUSES)})
