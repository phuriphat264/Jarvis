import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.personal_os import Task, CalendarEvent, Project
from app.database.models.iot import IoTDeviceState
from app.database.models.edge import EdgeNode
from app.world_model.schemas import WorldModelSnapshot

class ContextAggregator:
    @staticmethod
    async def get_snapshot(user_id: int, db: AsyncSession) -> WorldModelSnapshot:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        
        # Gather Tasks
        task_res = await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status != "DONE"
            ).order_by(Task.due_date.asc().nulls_last())
        )
        tasks = task_res.scalars().all()
        today_tasks = [
            {"id": t.id, "title": t.title, "priority": t.priority, "due_date": t.due_date.isoformat() if t.due_date else None} 
            for t in tasks if t.due_date and t.due_date < tomorrow_start
        ]

        # Gather Calendar
        cal_res = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_at >= now,
                CalendarEvent.start_at < now + timedelta(hours=24)
            ).order_by(CalendarEvent.start_at.asc())
        )
        events = cal_res.scalars().all()
        upcoming_events = [
            {"id": e.id, "title": e.title, "start_at": e.start_at.isoformat(), "end_at": e.end_at.isoformat() if e.end_at else None}
            for e in events
        ]
        
        # Gather IoT
        iot_res = await db.execute(select(IoTDeviceState))
        iot_states = iot_res.scalars().all()
        home_state = {
            "online_count": sum(1 for s in iot_states if s.online),
            "offline_count": sum(1 for s in iot_states if not s.online),
            "devices": [{"device_id": s.device_id, "power": s.power, "temp": s.temperature} for s in iot_states]
        }
        
        # Gather Edge
        edge_res = await db.execute(select(EdgeNode).where(EdgeNode.user_id == user_id))
        nodes = edge_res.scalars().all()
        edge_state = {
            "online_count": sum(1 for n in nodes if n.status == "ONLINE"),
            "nodes": [{"node_id": n.node_id, "status": n.status} for n in nodes]
        }
        
        return WorldModelSnapshot(
            current_time=now,
            today_tasks=today_tasks,
            upcoming_events=upcoming_events,
            active_projects=[], # Simplified for now
            home_state=home_state,
            edge_state=edge_state
        )
