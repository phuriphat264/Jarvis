import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal
from app.database.models.personal_os import Reminder, Notification

logger = logging.getLogger("jarvis.reminder_scheduler")

class ReminderScheduler:
    def __init__(self, poll_interval_seconds: int = 10):
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"ReminderScheduler started (poll_interval={self.poll_interval}s)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ReminderScheduler stopped")

    async def _loop(self):
        while self._running:
            try:
                await self._process_due_reminders()
            except Exception as e:
                logger.error(f"Error in ReminderScheduler: {e}")
            await asyncio.sleep(self.poll_interval)

    async def _process_due_reminders(self):
        now = datetime.now(timezone.utc)
        
        async with AsyncSessionLocal() as db:
            # Find due reminders that are pending
            result = await db.execute(
                select(Reminder)
                .where(Reminder.status == "PENDING", Reminder.remind_at <= now)
            )
            reminders = result.scalars().all()
            
            for reminder in reminders:
                # Mark as triggered
                reminder.status = "TRIGGERED"
                reminder.triggered_at = now
                
                # Create Notification
                notification = Notification(
                    user_id=reminder.user_id,
                    title=f"Reminder: {reminder.title}",
                    message=reminder.description or "",
                    type="REMINDER"
                )
                db.add(notification)
                
                logger.info(f"Triggered reminder {reminder.id} for user {reminder.user_id}")
                
            if reminders:
                await db.commit()

scheduler = ReminderScheduler()
