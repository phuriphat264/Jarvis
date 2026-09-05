from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class Situation(BaseModel):
    type: str # e.g. MEETING_SOON, DEADLINE_APPROACHING
    severity: str # LOW, NORMAL, HIGH, URGENT
    confidence: float
    metadata: Dict[str, Any] = {}

class WorldModelSnapshot(BaseModel):
    current_time: datetime
    situations: List[Situation] = []
    today_tasks: List[Dict[str, Any]] = []
    upcoming_events: List[Dict[str, Any]] = []
    active_projects: List[Dict[str, Any]] = []
    home_state: Dict[str, Any] = {}
    edge_state: Dict[str, Any] = {}
    recent_events: List[Dict[str, Any]] = []
