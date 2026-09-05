from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.personal_os import Task, Reminder, CalendarEvent

class PersonalOSContextBuilder:
    @staticmethod
    async def build_context(db: AsyncSession, user_id: int) -> str:
        """
        Builds a small, bounded summary of today's relevant personal OS context.
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 1. Overdue tasks
        overdue_r = await db.execute(
            select(Task)
            .where(Task.user_id == user_id, Task.status.in_(["TODO", "IN_PROGRESS"]), Task.due_at < today_start)
            .limit(5)
        )
        overdue = overdue_r.scalars().all()
        
        # 2. Today's tasks
        today_tasks_r = await db.execute(
            select(Task)
            .where(Task.user_id == user_id, Task.status.in_(["TODO", "IN_PROGRESS"]), Task.due_at >= today_start, Task.due_at < today_end)
            .limit(5)
        )
        today_tasks = today_tasks_r.scalars().all()
        
        # 3. Pending reminders (next 24h)
        reminders_r = await db.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.status == "PENDING", Reminder.remind_at >= today_start, Reminder.remind_at < today_end)
            .limit(5)
        )
        reminders = reminders_r.scalars().all()
        
        # 4. Today's calendar events
        events_r = await db.execute(
            select(CalendarEvent)
            .where(CalendarEvent.user_id == user_id, CalendarEvent.status == "ACTIVE", CalendarEvent.start_at >= today_start, CalendarEvent.start_at < today_end)
            .limit(5)
        )
        events = events_r.scalars().all()
        
        lines = ["--- PERSONAL OS SUMMARY (TODAY) ---"]
        
        if overdue:
            lines.append("Overdue Tasks:")
            for t in overdue:
                lines.append(f"- [ID:{t.id}] {t.title}")
        
        if today_tasks:
            lines.append("Today's Tasks:")
            for t in today_tasks:
                lines.append(f"- [ID:{t.id}] {t.title}")
                
        if reminders:
            lines.append("Upcoming Reminders:")
            for r in reminders:
                lines.append(f"- [ID:{r.id}] {r.title} at {r.remind_at.isoformat()}")
                
        if events:
            lines.append("Today's Events:")
            for e in events:
                lines.append(f"- [ID:{e.id}] {e.title} ({e.start_at.strftime('%H:%M')} - {e.end_at.strftime('%H:%M')})")
                
        if len(lines) == 1:
            return ""
            
        return "\n".join(lines) + "\n-----------------------------------"
