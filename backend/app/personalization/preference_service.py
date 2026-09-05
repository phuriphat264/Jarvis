"""
PreferenceService — CRUD layer for user_preferences.
All mutations are user-scoped; no cross-user access possible.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.models.personalization import UserPreference

logger = logging.getLogger("jarvis.preference_service")

# Priority constants
PRIORITY_USER_EXPLICIT = 100
PRIORITY_BEHAVIOR = 50


class PreferenceService:

    @staticmethod
    async def get_all(db: AsyncSession, user_id: int) -> List[UserPreference]:
        res = await db.execute(
            select(UserPreference)
            .where(UserPreference.user_id == user_id, UserPreference.status == "ACTIVE")
            .order_by(UserPreference.priority.desc())
        )
        return res.scalars().all()

    @staticmethod
    async def get_active_map(db: AsyncSession, user_id: int, scope: str = "GLOBAL") -> dict:
        """Return {key: value} for the highest-priority active preference per key."""
        res = await db.execute(
            select(UserPreference)
            .where(
                UserPreference.user_id == user_id,
                UserPreference.status == "ACTIVE",
                UserPreference.scope == scope,
            )
            .order_by(UserPreference.priority.desc())
        )
        prefs = res.scalars().all()
        pref_map: dict = {}
        for p in prefs:
            if p.key not in pref_map:  # First (highest priority) wins
                pref_map[p.key] = p.value
        return pref_map

    @staticmethod
    async def create_explicit(
        db: AsyncSession,
        user_id: int,
        key: str,
        value: str,
        scope: str = "GLOBAL",
        scope_id: Optional[str] = None,
    ) -> UserPreference:
        pref = UserPreference(
            user_id=user_id,
            key=key,
            value=value,
            scope=scope,
            scope_id=scope_id,
            source="USER_EXPLICIT",
            confidence=1.0,
            priority=PRIORITY_USER_EXPLICIT,
            status="ACTIVE",
        )
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
        logger.info(f"Explicit preference created: user={user_id} key={key} value={value}")
        return pref

    @staticmethod
    async def create_from_candidate(
        db: AsyncSession,
        user_id: int,
        key: str,
        value: str,
        confidence: float,
        scope: str = "GLOBAL",
    ) -> UserPreference:
        """Called when user approves a candidate suggestion."""
        pref = UserPreference(
            user_id=user_id,
            key=key,
            value=value,
            scope=scope,
            source="BEHAVIOR",
            confidence=confidence,
            priority=PRIORITY_BEHAVIOR,
            status="ACTIVE",
        )
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
        logger.info(f"Approved learned preference: user={user_id} key={key} value={value} conf={confidence}")
        return pref

    @staticmethod
    async def update(
        db: AsyncSession, user_id: int, pref_id: int, value: str
    ) -> Optional[UserPreference]:
        res = await db.execute(
            select(UserPreference).where(
                UserPreference.id == pref_id,
                UserPreference.user_id == user_id,
            )
        )
        pref = res.scalars().first()
        if not pref:
            return None
        pref.value = value
        pref.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(pref)
        return pref

    @staticmethod
    async def delete(db: AsyncSession, user_id: int, pref_id: int) -> bool:
        res = await db.execute(
            select(UserPreference).where(
                UserPreference.id == pref_id,
                UserPreference.user_id == user_id,
            )
        )
        pref = res.scalars().first()
        if not pref:
            return False
        pref.status = "ARCHIVED"
        await db.commit()
        logger.info(f"Preference archived: user={user_id} id={pref_id}")
        return True

    @staticmethod
    async def reset_learned(db: AsyncSession, user_id: int) -> int:
        """Archive all BEHAVIOR-sourced preferences. Explicit ones are untouched."""
        res = await db.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.source == "BEHAVIOR",
                UserPreference.status == "ACTIVE",
            )
        )
        prefs = res.scalars().all()
        for p in prefs:
            p.status = "ARCHIVED"
        await db.commit()
        logger.info(f"Reset {len(prefs)} learned preferences for user={user_id}")
        return len(prefs)
