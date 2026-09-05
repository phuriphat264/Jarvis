from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    status: Optional[str] = "TODO"
    priority: Optional[str] = "MEDIUM"
    due_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    user_id: int
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    target_date: Optional[datetime] = None
    progress: Optional[float] = 0.0

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    target_date: Optional[datetime] = None
    progress: Optional[float] = None

class GoalResponse(GoalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class NoteBase(BaseModel):
    title: str
    content: str
    category: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class NoteResponse(NoteBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ReminderBase(BaseModel):
    title: str
    description: Optional[str] = None
    remind_at: datetime

class ReminderCreate(ReminderBase):
    pass

class ReminderResponse(ReminderBase):
    id: int
    user_id: int
    status: str
    triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CalendarEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_at: datetime
    end_at: datetime
    all_day: Optional[bool] = False
    location: Optional[str] = None

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = None
    status: Optional[str] = None

class CalendarEventResponse(CalendarEventBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: Optional[str]
    type: str
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    today_tasks: List[TaskResponse]
    overdue_tasks: List[TaskResponse]
    upcoming_reminders: List[ReminderResponse]
    today_events: List[CalendarEventResponse]
    active_projects: List[ProjectResponse]
    active_goals: List[GoalResponse]
