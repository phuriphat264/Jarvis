from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class IntegrationConnectionResponse(BaseModel):
    id: int
    provider: str
    status: str
    display_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PendingActionResponse(BaseModel):
    id: int
    tool_name: str
    description: str
    arguments: Dict[str, Any]
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationPreferenceSchema(BaseModel):
    in_app_enabled: bool = True
    line_enabled: bool = False
    telegram_enabled: bool = False
    email_enabled: bool = False
    quiet_hours_enabled: bool = True
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    daily_summary_enabled: bool = True
    meeting_reminder_enabled: bool = True
    task_overdue_enabled: bool = True
    
    class Config:
        from_attributes = True
