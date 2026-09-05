"""
AdaptationEngine — Loads active preferences and builds a compact personalization
context string to inject into the LLM system prompt.

Priority order (highest → lowest):
  1. Safety Policy   (enforced elsewhere; not touched here)
  2. Explicit Current Instruction   (handled by ContextManager conversation history)
  3. Explicit Stored Preference     (source=USER_EXPLICIT, priority=100)
  4. Contextual Learned Preference  (scope=PROJECT/CONVERSATION, source=BEHAVIOR)
  5. Global Learned Preference      (scope=GLOBAL, source=BEHAVIOR)
  6. Default system behavior        (nothing injected)
"""
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.personalization.preference_service import PreferenceService
from app.core.config import settings

logger = logging.getLogger("jarvis.adaptation_engine")

# Human-readable labels for the LLM context block
_KEY_LABELS = {
    "response_length": "Response length",
    "language": "Language",
    "tone": "Tone",
    "formatting": "Formatting",
    "planning_style": "Planning preference",
    "notification_frequency": "Notification frequency",
    "interface_preference": "Interface",
    "routine_suggestions": "Routine suggestions",
    "iot_suggestions": "IoT suggestions",
    "voice_speed": "Voice speed",
    "research_detail": "Research detail level",
}

# Human-readable value labels
_VALUE_LABELS = {
    "short": "Short / concise",
    "detailed": "Detailed",
    "th": "Thai (ภาษาไทย)",
    "en": "English",
    "friendly": "Friendly",
    "formal": "Formal",
    "bullet_points": "Bullet points",
    "prose": "Prose",
    "priority_first": "Priority first",
    "deadline_first": "Deadline first",
    "low": "Low frequency",
    "high": "High frequency",
    "voice": "Voice",
    "text": "Text",
    "enabled": "Enabled",
    "disabled": "Disabled",
    "normal": "Normal speed",
    "fast": "Fast",
    "slow": "Slow",
    "medium": "Medium detail",
}


class AdaptationEngine:

    @staticmethod
    async def get_context(user_id: int, db: AsyncSession) -> str:
        """Return a compact personalization context block for the system prompt."""
        if not settings.PERSONALIZATION_ENABLED:
            return ""

        try:
            pref_map = await PreferenceService.get_active_map(db, user_id, scope="GLOBAL")
            if not pref_map:
                return ""

            lines = ["PERSONALIZATION:"]
            for key, value in pref_map.items():
                label = _KEY_LABELS.get(key, key.replace("_", " ").title())
                val_label = _VALUE_LABELS.get(value, value)
                lines.append(f"  {label}: {val_label}")

            return "\n".join(lines)

        except Exception as e:
            logger.warning(f"AdaptationEngine failed gracefully: {e}")
            return ""  # Fail open — never interrupt the user's request

    @staticmethod
    async def get_profile(user_id: int, db: AsyncSession) -> dict:
        """Return structured profile dict for the API."""
        if not settings.PERSONALIZATION_ENABLED:
            return {}

        pref_map = await PreferenceService.get_active_map(db, user_id, scope="GLOBAL")
        profile: dict = {
            "response": {},
            "planning": {},
            "notifications": {},
            "voice": {},
        }

        mapping = {
            "response_length": ("response", "length"),
            "language": ("response", "language"),
            "tone": ("response", "tone"),
            "formatting": ("response", "format"),
            "planning_style": ("planning", "style"),
            "notification_frequency": ("notifications", "frequency"),
            "voice_speed": ("voice", "speed"),
            "interface_preference": ("voice", "preferred_interface"),
        }

        for key, value in pref_map.items():
            if key in mapping:
                section, field = mapping[key]
                profile[section][field] = value

        return {k: v for k, v in profile.items() if v}
