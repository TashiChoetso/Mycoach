from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_request_id
from app.models.engagement import UserEvent


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def emit(
        self,
        *,
        user_id: uuid.UUID,
        event_type: str,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
    ) -> UserEvent:
        now = datetime.now(UTC)
        event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            occurred_at=now,
            entity_type=entity_type,
            entity_id=entity_id,
            idempotency_key=idempotency_key,
            event_metadata=metadata or {},
            request_id=get_request_id(),
            created_at=now,
        )
        self.db.add(event)
        await self.db.flush()
        return event
