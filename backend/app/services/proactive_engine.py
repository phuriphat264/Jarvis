import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal
from app.world_model.context_aggregator import ContextAggregator
from app.world_model.situation_engine import SituationEngine
from app.world_model.proactive_decision_engine import ProactiveDecisionEngine
from app.database.models.user import User

logger = logging.getLogger("jarvis.proactive_engine")

class ProactiveEngine:
    def __init__(self, poll_interval_seconds: int = 60):
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Phase 16 ProactiveEngine started (poll_interval={self.poll_interval}s)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ProactiveEngine stopped")

    async def _loop(self):
        while self._running:
            try:
                await self._process_world_model_loop()
            except Exception as e:
                logger.error(f"Error in ProactiveEngine: {e}")
            await asyncio.sleep(self.poll_interval)

    async def _process_world_model_loop(self):
        # We iterate over all active users in a real system. 
        # For this prototype, we'll fetch all users.
        async with AsyncSessionLocal() as db:
            users_res = await db.execute(select(User))
            users = users_res.scalars().all()
            
            for u in users:
                # 1. Aggregate Context
                snapshot = await ContextAggregator.get_snapshot(u.id, db)
                
                # 2. Detect Situations
                snapshot.situations = SituationEngine.detect_situations(snapshot)
                
                # 3. Make Proactive Decisions
                await ProactiveDecisionEngine.evaluate_and_generate(u.id, snapshot, db)

proactive_engine = ProactiveEngine()
