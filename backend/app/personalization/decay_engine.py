"""
DecayEngine — Archives stale BEHAVIOR-sourced preferences.

Rules:
- Only decays BEHAVIOR preferences (never USER_EXPLICIT).
- Decay is linear over PREFERENCE_DECAY_DAYS of inactivity.
- When decayed confidence < 0.15, preference is archived.
- This runs as a background task (called from ProactiveEngine or a cron).
"""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.models.personalization import UserPreference
from app.personalization.confidence_engine import ConfidenceEngine
from app.core.config import settings

logger = logging.getLogger("jarvis.decay_engine")

ARCHIVE_THRESHOLD = 0.15


class DecayEngine:

    @staticmethod
    async def run_decay(db: AsyncSession) -> int:
        """Decay all stale BEHAVIOR preferences across all users. Returns archived count."""
        if not settings.PREFERENCE_DECAY_ENABLED:
            return 0

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=settings.PREFERENCE_DECAY_DAYS)

        res = await db.execute(
            select(UserPreference).where(
                UserPreference.source == "BEHAVIOR",
                UserPreference.status == "ACTIVE",
            )
        )
        prefs = res.scalars().all()

        archived = 0
        for p in prefs:
            last_active = p.last_used_at or p.updated_at or p.created_at
            if last_active and last_active < cutoff:
                days_inactive = (now - last_active).days
                new_conf = ConfidenceEngine.decay(
                    p.confidence, days_inactive, settings.PREFERENCE_DECAY_DAYS
                )
                if new_conf < ARCHIVE_THRESHOLD:
                    p.status = "ARCHIVED"
                    archived += 1
                    logger.info(
                        f"Preference archived by decay: user={p.user_id} "
                        f"key={p.key} conf={new_conf}"
                    )
                else:
                    p.confidence = new_conf

        if archived > 0 or prefs:
            await db.commit()

        return archived
