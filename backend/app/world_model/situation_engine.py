from datetime import datetime, timezone, timedelta
from typing import List
from app.world_model.schemas import WorldModelSnapshot, Situation

class SituationEngine:
    @staticmethod
    def detect_situations(snapshot: WorldModelSnapshot) -> List[Situation]:
        situations = []
        now = snapshot.current_time
        
        # 1. Meeting Soon
        if snapshot.upcoming_events:
            next_event = snapshot.upcoming_events[0]
            start_at = datetime.fromisoformat(next_event["start_at"])
            diff_minutes = (start_at - now).total_seconds() / 60
            
            if 0 <= diff_minutes <= 15:
                situations.append(Situation(
                    type="MEETING_SOON",
                    severity="HIGH",
                    confidence=1.0,
                    metadata={"event_id": next_event["id"], "title": next_event["title"], "starts_in": int(diff_minutes)}
                ))
                
        # 2. Deadline Approaching
        urgent_tasks = []
        for task in snapshot.today_tasks:
            if task.get("due_date"):
                due = datetime.fromisoformat(task["due_date"])
                diff_hours = (due - now).total_seconds() / 3600
                if 0 <= diff_hours <= 4:
                    urgent_tasks.append(task)
                    
        if urgent_tasks:
            situations.append(Situation(
                type="DEADLINE_APPROACHING",
                severity="HIGH" if len(urgent_tasks) > 1 else "NORMAL",
                confidence=0.95,
                metadata={"tasks": [t["title"] for t in urgent_tasks]}
            ))
            
        # 3. Home Idle / Active (Simplified)
        if snapshot.home_state:
            active_devices = sum(1 for d in snapshot.home_state.get("devices", []) if d.get("power"))
            if active_devices == 0:
                situations.append(Situation(type="HOME_IDLE", severity="LOW", confidence=0.8))
            else:
                situations.append(Situation(type="HOME_ACTIVE", severity="LOW", confidence=0.8, metadata={"active_count": active_devices}))
                
        # 4. Edge Offline
        if snapshot.edge_state.get("online_count") == 0 and snapshot.edge_state.get("nodes"):
            situations.append(Situation(type="EDGE_OFFLINE", severity="NORMAL", confidence=1.0))
            
        return situations
