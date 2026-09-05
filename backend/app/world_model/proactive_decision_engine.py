from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from app.database.models.world_model import ProactiveRecommendation, IntelligenceSettings
from app.world_model.schemas import WorldModelSnapshot
import logging

logger = logging.getLogger("jarvis.proactive_decision")

class ProactiveDecisionEngine:
    @staticmethod
    async def evaluate_and_generate(user_id: int, snapshot: WorldModelSnapshot, db: AsyncSession):
        # Fetch settings
        settings_res = await db.execute(select(IntelligenceSettings).where(IntelligenceSettings.user_id == user_id))
        settings = settings_res.scalars().first()
        if not settings or not settings.proactive_assistant_enabled:
            return

        # Quiet Hours check
        if ProactiveDecisionEngine._in_quiet_hours(settings, snapshot.current_time):
            return

        for situation in snapshot.situations:
            # Policy 1: Meeting Soon
            if situation.type == "MEETING_SOON":
                fingerprint = f"MEETING_SOON:{situation.metadata['event_id']}"
                await ProactiveDecisionEngine._issue_recommendation(
                    db=db, user_id=user_id,
                    type="MEETING_SOON",
                    message=f"Upcoming Meeting: {situation.metadata['title']} in {situation.metadata['starts_in']} minutes.",
                    reason=situation.dict(),
                    priority="HIGH",
                    fingerprint=fingerprint,
                    cooldown_minutes=60
                )
                
            # Policy 2: Deadline Approaching
            if situation.type == "DEADLINE_APPROACHING" and settings.deadline_warnings_enabled:
                task_titles = ", ".join(situation.metadata['tasks'])
                fingerprint = f"DEADLINE_APPROACHING:{snapshot.current_time.strftime('%Y-%m-%d')}"
                await ProactiveDecisionEngine._issue_recommendation(
                    db=db, user_id=user_id,
                    type="DEADLINE_WARNING",
                    message=f"You have approaching deadlines today: {task_titles}.",
                    reason=situation.dict(),
                    priority="HIGH" if situation.severity == "HIGH" else "NORMAL",
                    fingerprint=fingerprint,
                    cooldown_minutes=240 # Only warn every 4 hours
                )
                
            # Policy 3: Edge Offline
            if situation.type == "EDGE_OFFLINE":
                fingerprint = f"EDGE_OFFLINE:{snapshot.current_time.strftime('%Y-%m-%d')}"
                await ProactiveDecisionEngine._issue_recommendation(
                    db=db, user_id=user_id,
                    type="EDGE_OFFLINE_WARNING",
                    message="Your JARVIS Edge node is currently offline.",
                    reason=situation.dict(),
                    priority="NORMAL",
                    fingerprint=fingerprint,
                    cooldown_minutes=720 # Warn every 12 hours
                )

        await db.commit()

    @staticmethod
    async def _issue_recommendation(db: AsyncSession, user_id: int, type: str, message: str, reason: dict, priority: str, fingerprint: str, cooldown_minutes: int):
        # Anti-spam Deduplication & Cooldown check
        now = datetime.now(timezone.utc)
        threshold_time = now - timedelta(minutes=cooldown_minutes)
        
        existing_res = await db.execute(
            select(ProactiveRecommendation).where(
                ProactiveRecommendation.user_id == user_id,
                ProactiveRecommendation.fingerprint == fingerprint,
                ProactiveRecommendation.created_at >= threshold_time
            )
        )
        if existing_res.scalars().first():
            return # Skip, cooldown active
            
        rec = ProactiveRecommendation(
            user_id=user_id,
            type=type,
            message=message,
            reason=reason,
            priority=priority,
            fingerprint=fingerprint,
            status="ACTIVE"
        )
        db.add(rec)
        logger.info(f"Issued Proactive Recommendation: {message}")

    @staticmethod
    def _in_quiet_hours(settings: IntelligenceSettings, now: datetime) -> bool:
        try:
            start_hour, start_min = map(int, settings.quiet_hours_start.split(":"))
            end_hour, end_min = map(int, settings.quiet_hours_end.split(":"))
            
            # Simple hour check logic
            current_hour = now.hour
            if start_hour > end_hour:
                return current_hour >= start_hour or current_hour < end_hour
            else:
                return start_hour <= current_hour < end_hour
        except:
            return False
