from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, or_, and_

from app.database.session import get_db
from app.database.models.user import User
from app.database.models.personal_os import Project, Task, Goal, Note, Reminder, CalendarEvent, Notification
from app.database.models.activity_log import ActivityLog
from app.schemas.personal_os import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    GoalCreate, GoalUpdate, GoalResponse,
    NoteCreate, NoteUpdate, NoteResponse,
    ReminderCreate, ReminderResponse,
    CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse,
    NotificationResponse, DashboardResponse
)
from app.core.dependencies import get_current_user

router = APIRouter()

def log_activity(db, user_id, action, details):
    log = ActivityLog(user_id=user_id, action=action, details=details)
    db.add(log)

# --- Tasks ---
@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(status: Optional[str] = None, project_id: Optional[int] = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Task).where(Task.user_id == current_user.id)
    if status:
        query = query.where(Task.status == status)
    if project_id:
        query = query.where(Task.project_id == project_id)
    query = query.order_by(Task.due_at.asc().nulls_last())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = Task(**task_in.model_dump(), user_id=current_user.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    log_activity(db, current_user.id, "TASK_CREATED", {"task_id": task.id})
    await db.commit()
    return task

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_in: TaskUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    for k, v in task_in.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
        
    await db.commit()
    await db.refresh(task)
    log_activity(db, current_user.id, "TASK_UPDATED", {"task_id": task.id})
    await db.commit()
    return task

@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.status = "DONE"
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    log_activity(db, current_user.id, "TASK_COMPLETED", {"task_id": task.id})
    await db.commit()
    return task

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.status = "DELETED"
    await db.commit()
    log_activity(db, current_user.id, "TASK_DELETED", {"task_id": task_id})
    await db.commit()
    return {"success": True}

# --- Projects ---
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(status: Optional[str] = "ACTIVE", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Project).where(Project.user_id == current_user.id)
    if status:
        query = query.where(Project.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/projects", response_model=ProjectResponse)
async def create_project(proj_in: ProjectCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    proj = Project(**proj_in.model_dump(), user_id=current_user.id)
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    log_activity(db, current_user.id, "PROJECT_CREATED", {"project_id": proj.id})
    await db.commit()
    return proj

@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, proj_in: ProjectUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == current_user.id))
    proj = result.scalars().first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    for k, v in proj_in.model_dump(exclude_unset=True).items():
        setattr(proj, k, v)
        
    await db.commit()
    await db.refresh(proj)
    log_activity(db, current_user.id, "PROJECT_UPDATED", {"project_id": proj.id})
    await db.commit()
    return proj

# --- Goals ---
@router.get("/goals", response_model=List[GoalResponse])
async def list_goals(status: Optional[str] = "ACTIVE", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Goal).where(Goal.user_id == current_user.id)
    if status:
        query = query.where(Goal.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/goals", response_model=GoalResponse)
async def create_goal(goal_in: GoalCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    goal = Goal(**goal_in.model_dump(), user_id=current_user.id)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal

@router.patch("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: int, goal_in: GoalUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id))
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    for k, v in goal_in.model_dump(exclude_unset=True).items():
        setattr(goal, k, v)
        
    await db.commit()
    await db.refresh(goal)
    log_activity(db, current_user.id, "GOAL_UPDATED", {"goal_id": goal.id})
    await db.commit()
    return goal

# --- Notes ---
@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.user_id == current_user.id, Note.status == "ACTIVE").order_by(desc(Note.updated_at)))
    return result.scalars().all()

@router.post("/notes", response_model=NoteResponse)
async def create_note(note_in: NoteCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    note = Note(**note_in.model_dump(), user_id=current_user.id)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    # Simple semantic indexing background task if we had one.
    
    log_activity(db, current_user.id, "NOTE_CREATED", {"note_id": note.id})
    await db.commit()
    return note

@router.patch("/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note_in: NoteUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == current_user.id))
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    for k, v in note_in.model_dump(exclude_unset=True).items():
        setattr(note, k, v)
        
    await db.commit()
    await db.refresh(note)
    log_activity(db, current_user.id, "NOTE_UPDATED", {"note_id": note.id})
    await db.commit()
    return note

@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == current_user.id))
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    note.status = "DELETED"
    await db.commit()
    log_activity(db, current_user.id, "NOTE_DELETED", {"note_id": note.id})
    await db.commit()
    return {"success": True}

@router.get("/notes/search", response_model=List[NoteResponse])
async def search_notes(query: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Semantic search reusing EmbeddingProvider
    from app.interfaces.embedding_provider import EmbeddingProviderFactory
    provider = EmbeddingProviderFactory.get_provider()
    embedding = await provider.embed_query(query)
    
    # We query the pgvector if it's set up
    result = await db.execute(
        select(Note)
        .where(Note.user_id == current_user.id, Note.status == "ACTIVE", Note.embedding != None)
        .order_by(Note.embedding.cosine_distance(embedding))
        .limit(5)
    )
    notes = result.scalars().all()
    # If no embeddings, fallback to ilike
    if not notes:
        result = await db.execute(
            select(Note)
            .where(Note.user_id == current_user.id, Note.status == "ACTIVE", Note.content.ilike(f"%{query}%"))
            .limit(5)
        )
        notes = result.scalars().all()
        
    return notes

# --- Reminders ---
@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(status: Optional[str] = "PENDING", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Reminder).where(Reminder.user_id == current_user.id)
    if status:
        query = query.where(Reminder.status == status)
    query = query.order_by(Reminder.remind_at)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/reminders", response_model=ReminderResponse)
async def create_reminder(reminder_in: ReminderCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    reminder = Reminder(**reminder_in.model_dump(), user_id=current_user.id)
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    log_activity(db, current_user.id, "REMINDER_CREATED", {"reminder_id": reminder.id})
    await db.commit()
    return reminder

@router.post("/reminders/{reminder_id}/cancel")
async def cancel_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id))
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    reminder.status = "CANCELLED"
    await db.commit()
    log_activity(db, current_user.id, "REMINDER_CANCELLED", {"reminder_id": reminder.id})
    await db.commit()
    return {"success": True}

# --- Calendar Events ---
@router.get("/calendar/events", response_model=List[CalendarEventResponse])
async def list_events(start: datetime, end: datetime, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.status == "ACTIVE",
            CalendarEvent.start_at >= start,
            CalendarEvent.start_at <= end
        )
        .order_by(CalendarEvent.start_at)
    )
    return result.scalars().all()

@router.post("/calendar/events", response_model=CalendarEventResponse)
async def create_event(event_in: CalendarEventCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    event = CalendarEvent(**event_in.model_dump(), user_id=current_user.id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    log_activity(db, current_user.id, "CALENDAR_EVENT_CREATED", {"event_id": event.id})
    await db.commit()
    return event

@router.patch("/calendar/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(event_id: int, event_in: CalendarEventUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    for k, v in event_in.model_dump(exclude_unset=True).items():
        setattr(event, k, v)
        
    await db.commit()
    await db.refresh(event)
    log_activity(db, current_user.id, "CALENDAR_EVENT_UPDATED", {"event_id": event.id})
    await db.commit()
    return event

@router.delete("/calendar/events/{event_id}")
async def delete_event(event_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event.status = "CANCELLED"
    await db.commit()
    log_activity(db, current_user.id, "CALENDAR_EVENT_DELETED", {"event_id": event.id})
    await db.commit()
    return {"success": True}

# --- Dashboard & Notifications ---
@router.get("/notifications", response_model=List[NotificationResponse])
async def list_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(20)
    )
    return result.scalars().all()

@router.post("/notifications/{notif_id}/read")
async def read_notification(notif_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notif_id, Notification.user_id == current_user.id))
    notif = result.scalars().first()
    if notif:
        notif.read_at = datetime.now(timezone.utc)
        await db.commit()
    return {"success": True}

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Today's tasks
    r = await db.execute(select(Task).where(Task.user_id == current_user.id, Task.status.in_(["TODO", "IN_PROGRESS"]), Task.due_at >= today_start, Task.due_at < today_end))
    today_tasks = r.scalars().all()
    
    # Overdue tasks
    r = await db.execute(select(Task).where(Task.user_id == current_user.id, Task.status.in_(["TODO", "IN_PROGRESS"]), Task.due_at < today_start))
    overdue_tasks = r.scalars().all()
    
    # Reminders
    r = await db.execute(select(Reminder).where(Reminder.user_id == current_user.id, Reminder.status == "PENDING", Reminder.remind_at >= today_start, Reminder.remind_at < today_start + timedelta(days=7)))
    upcoming_reminders = r.scalars().all()
    
    # Events
    r = await db.execute(select(CalendarEvent).where(CalendarEvent.user_id == current_user.id, CalendarEvent.status == "ACTIVE", CalendarEvent.start_at >= today_start, CalendarEvent.start_at < today_end))
    today_events = r.scalars().all()
    
    # Active Projects
    r = await db.execute(select(Project).where(Project.user_id == current_user.id, Project.status == "ACTIVE"))
    active_projects = r.scalars().all()
    
    # Active Goals
    r = await db.execute(select(Goal).where(Goal.user_id == current_user.id, Goal.status == "ACTIVE"))
    active_goals = r.scalars().all()
    
    return {
        "today_tasks": today_tasks,
        "overdue_tasks": overdue_tasks,
        "upcoming_reminders": upcoming_reminders,
        "today_events": today_events,
        "active_projects": active_projects,
        "active_goals": active_goals
    }
