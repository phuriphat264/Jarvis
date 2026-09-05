"""
BehaviorTracker — Records lightweight, privacy-safe behavioral signals.

Rules:
- Never store raw message content.
- Never store credentials or PII.
- Only structured metadata (event type, entity IDs, context labels).
- Rate-limited to MAX_BEHAVIOR_EVENTS_PER_DAY per user.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database.models.personalization import BehaviorEvent
from app.core.config import settings

logger = logging.getLogger("jarvis.behavior_tracker")

# Event types (importable constants)
RESPONSE_SHORTENED = "RESPONSE_SHORTENED"
RESPONSE_EXPANDED = "RESPONSE_EXPANDED"
RESPONSE_REGENERATED = "RESPONSE_REGENERATED"
RECOMMENDATION_ACCEPTED = "RECOMMENDATION_ACCEPTED"
RECOMMENDATION_REJECTED = "RECOMMENDATION_REJECTED"
RECOMMENDATION_DISMISSED = "RECOMMENDATION_DISMISSED"
TASK_REORDERED = "TASK_REORDERED"
TASK_COMPLETED = "TASK_COMPLETED"
NOTIFICATION_DISMISSED = "NOTIFICATION_DISMISSED"
NOTIFICATION_SNOOZED = "NOTIFICATION_SNOOZED"
VOICE_USED = "VOICE_USED"
TEXT_USED = "TEXT_USED"
ROUTINE_ACCEPTED = "ROUTINE_ACCEPTED"
ROUTINE_REJECTED = "ROUTINE_REJECTED"
IOT_SUGGESTION_ACCEPTED = "IOT_SUGGESTION_ACCEPTED"
IOT_SUGGESTION_REJECTED = "IOT_SUGGESTION_REJECTED"


class BehaviorTracker:

    @staticmethod
    async def record(
        db: AsyncSession,
        user_id: int,
        event_type: str,
        context: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[BehaviorEvent]:
        if not settings.BEHAVIOR_LEARNING_ENABLED:
            return None

        # Daily rate limit
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count_res = await db.execute(
            select(func.count(BehaviorEvent.id)).where(
                BehaviorEvent.user_id == user_id,
                BehaviorEvent.created_at >= today_start,
            )
        )
        daily_count = count_res.scalar() or 0
        if daily_count >= settings.MAX_BEHAVIOR_EVENTS_PER_DAY:
            logger.warning(f"Daily behavior event limit reached for user={user_id}")
            return None

        # Strip any raw content from metadata (safety guard)
        safe_metadata = {}
        if metadata:
            for k, v in metadata.items():
                if k in ("key", "value", "context", "event_subtype", "count"):
                    safe_metadata[k] = v

        event = BehaviorEvent(
            user_id=user_id,
            event_type=event_type,
            context=context,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            metadata=safe_metadata or None,
        )
        db.add(event)
        await db.commit()
        return event

    @staticmethod
    async def count_recent(
        db: AsyncSession,
        user_id: int,
        event_type: str,
        days: int = 30,
        metadata_key: Optional[str] = None,
        metadata_value: Optional[str] = None,
    ) -> int:
        """Count occurrences of an event type in the last N days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        q = select(func.count(BehaviorEvent.id)).where(
            BehaviorEvent.user_id == user_id,
            BehaviorEvent.event_type == event_type,
            BehaviorEvent.created_at >= since,
        )
        res = await db.execute(q)
        return res.scalar() or 0
