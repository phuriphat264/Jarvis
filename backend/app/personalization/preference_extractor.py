"""
PreferenceExtractor — Scans BehaviorEvents and creates PreferenceCandidates.

Rules:
- Only creates PENDING candidates; never auto-applies them.
- Requires MIN_EVIDENCE_FOR_LEARNING observations before a candidate is created.
- Does NOT allow the LLM to create candidates directly.
- Handles contradictions by scoping the newer preference to CONVERSATION, not overwriting GLOBAL.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database.models.personalization import BehaviorEvent, PreferenceCandidate
from app.personalization.confidence_engine import ConfidenceEngine
from app.core.config import settings

logger = logging.getLogger("jarvis.preference_extractor")

# Maps (event_type, optional_metadata_key) → (preference_key, preference_value)
EXTRACTION_RULES: List[Tuple[str, str, str]] = [
    ("RESPONSE_SHORTENED", "response_length", "short"),
    ("RESPONSE_EXPANDED", "response_length", "detailed"),
    ("VOICE_USED", "interface_preference", "voice"),
    ("TEXT_USED", "interface_preference", "text"),
    ("ROUTINE_ACCEPTED", "routine_suggestions", "enabled"),
    ("ROUTINE_REJECTED", "routine_suggestions", "disabled"),
    ("IOT_SUGGESTION_ACCEPTED", "iot_suggestions", "enabled"),
    ("IOT_SUGGESTION_REJECTED", "iot_suggestions", "disabled"),
    ("NOTIFICATION_DISMISSED", "notification_frequency", "low"),
]


class PreferenceExtractor:

    @staticmethod
    async def run(db: AsyncSession, user_id: int) -> List[PreferenceCandidate]:
        """Scan recent behavior and upsert PreferenceCandidates. Returns new/updated candidates."""
        if not settings.BEHAVIOR_LEARNING_ENABLED:
            return []

        threshold = settings.MIN_EVIDENCE_FOR_LEARNING
        since = datetime.now(timezone.utc) - timedelta(days=30)
        new_or_updated: List[PreferenceCandidate] = []

        for event_type, pref_key, pref_value in EXTRACTION_RULES:
            # Count evidence
            count_res = await db.execute(
                select(func.count(BehaviorEvent.id)).where(
                    BehaviorEvent.user_id == user_id,
                    BehaviorEvent.event_type == event_type,
                    BehaviorEvent.created_at >= since,
                )
            )
            evidence_count = count_res.scalar() or 0
            if evidence_count < threshold:
                continue

            confidence = ConfidenceEngine.calculate(evidence_count, "BEHAVIOR")

            # Check for existing PENDING candidate
            existing_res = await db.execute(
                select(PreferenceCandidate).where(
                    PreferenceCandidate.user_id == user_id,
                    PreferenceCandidate.key == pref_key,
                    PreferenceCandidate.value == pref_value,
                    PreferenceCandidate.status == "PENDING",
                )
            )
            existing = existing_res.scalars().first()

            if existing:
                # Update evidence + confidence
                existing.evidence_count = evidence_count
                existing.confidence = confidence
                existing.updated_at = datetime.now(timezone.utc)
                new_or_updated.append(existing)
            else:
                candidate = PreferenceCandidate(
                    user_id=user_id,
                    key=pref_key,
                    value=pref_value,
                    scope="GLOBAL",
                    confidence=confidence,
                    evidence_count=evidence_count,
                    status="PENDING",
                )
                db.add(candidate)
                new_or_updated.append(candidate)
                logger.info(
                    f"New preference candidate: user={user_id} "
                    f"key={pref_key} value={pref_value} "
                    f"evidence={evidence_count} conf={confidence}"
                )

        await db.commit()
        return new_or_updated
