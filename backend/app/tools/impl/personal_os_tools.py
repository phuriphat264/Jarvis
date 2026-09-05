from typing import Dict, Any, List
from datetime import datetime, timezone
import dateutil.parser

from sqlalchemy.future import select
from sqlalchemy import desc

from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult
from app.database.session import AsyncSessionLocal
from app.database.models.personal_os import Task, Project, Goal, Reminder, CalendarEvent, Note
from app.database.models.activity_log import ActivityLog

def parse_date(date_str: str) -> datetime:
    dt = dateutil.parser.parse(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

class DashboardGetTool(BaseTool):
    name = "dashboard_get"
    description = "Get the user's personal OS dashboard summary including today's tasks, overdue tasks, events, and pending reminders."
    category = "personal_os"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                from app.api.v1.personal_os import get_dashboard
                # We can replicate logic since we need internal objects converted to dict
                now = datetime.now(timezone.utc)
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                from datetime import timedelta
                today_end = today_start + timedelta(days=1)
                
                tasks_r = await db.execute(select(Task).where(Task.user_id == context.user_id, Task.status.in_(["TODO", "IN_PROGRESS"]), Task.due_at >= today_start, Task.due_at < today_end))
                overdue_r = await db.execute(select(Task).where(Task.user_id == context.user_id, Task.status.in_(["TODO", "IN_PROGRESS"]), Task.due_at < today_start))
                events_r = await db.execute(select(CalendarEvent).where(CalendarEvent.user_id == context.user_id, CalendarEvent.status == "ACTIVE", CalendarEvent.start_at >= today_start, CalendarEvent.start_at < today_end))
                reminders_r = await db.execute(select(Reminder).where(Reminder.user_id == context.user_id, Reminder.status == "PENDING"))
                
                return ToolExecutionResult(
                    success=True, 
                    tool_name=self.name, 
                    data={
                        "today_tasks": [{"id": t.id, "title": t.title, "due": str(t.due_at)} for t in tasks_r.scalars().all()],
                        "overdue_tasks": [{"id": t.id, "title": t.title, "due": str(t.due_at)} for t in overdue_r.scalars().all()],
                        "today_events": [{"id": e.id, "title": e.title, "start": str(e.start_at), "end": str(e.end_at)} for e in events_r.scalars().all()],
                        "pending_reminders": [{"id": r.id, "title": r.title, "remind_at": str(r.remind_at)} for r in reminders_r.scalars().all()]
                    }
                )
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class TaskCreateTool(BaseTool):
    name = "task_create"
    description = "Create a new task for the user."
    category = "personal_os"
    permission_level = "write"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string"},
                "due_at": {"type": "string", "description": "ISO 8601 datetime format for due date, e.g. 2026-09-06T09:00:00Z"},
                "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"]},
                "project_id": {"type": "integer"}
            },
            "required": ["title"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                due_at = parse_date(arguments["due_at"]) if "due_at" in arguments else None
                task = Task(
                    user_id=context.user_id,
                    title=arguments["title"],
                    description=arguments.get("description"),
                    due_at=due_at,
                    priority=arguments.get("priority", "MEDIUM"),
                    project_id=arguments.get("project_id")
                )
                db.add(task)
                db.add(ActivityLog(user_id=context.user_id, action="TASK_CREATED"))
                await db.commit()
                return ToolExecutionResult(success=True, tool_name=self.name, data={"id": task.id, "title": task.title, "status": "CREATED"})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class TaskListTool(BaseTool):
    name = "task_list"
    description = "List tasks for the user. Optionally filter by status."
    category = "personal_os"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "TODO, IN_PROGRESS, DONE"}
            }
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                q = select(Task).where(Task.user_id == context.user_id)
                if "status" in arguments:
                    q = q.where(Task.status == arguments["status"])
                r = await db.execute(q)
                tasks = [{"id": t.id, "title": t.title, "status": t.status, "due": str(t.due_at)} for t in r.scalars().all()]
                return ToolExecutionResult(success=True, tool_name=self.name, data={"tasks": tasks})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class TaskUpdateTool(BaseTool):
    name = "task_update"
    description = "Update an existing task."
    category = "personal_os"
    permission_level = "write"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "status": {"type": "string", "description": "TODO, IN_PROGRESS, DONE"},
                "title": {"type": "string"},
                "due_at": {"type": "string"}
            },
            "required": ["task_id"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                r = await db.execute(select(Task).where(Task.id == arguments["task_id"], Task.user_id == context.user_id))
                task = r.scalars().first()
                if not task:
                    return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_FOUND", "message": "Task not found"})
                if "status" in arguments: task.status = arguments["status"]
                if "title" in arguments: task.title = arguments["title"]
                if "due_at" in arguments: task.due_at = parse_date(arguments["due_at"])
                await db.commit()
                return ToolExecutionResult(success=True, tool_name=self.name, data={"id": task.id, "status": "UPDATED"})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class TaskCompleteTool(BaseTool):
    name = "task_complete"
    description = "Mark a task as DONE."
    category = "personal_os"
    permission_level = "write"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"}
            },
            "required": ["task_id"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                r = await db.execute(select(Task).where(Task.id == arguments["task_id"], Task.user_id == context.user_id))
                task = r.scalars().first()
                if not task:
                    return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_FOUND", "message": "Task not found"})
                task.status = "DONE"
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return ToolExecutionResult(success=True, tool_name=self.name, data={"id": task.id, "status": "COMPLETED"})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class ReminderCreateTool(BaseTool):
    name = "reminder_create"
    description = "Create a new reminder to notify the user at a specific time. Ensure you convert relative time (e.g. 'พรุ่งนี้ 9 โมง') to an exact absolute ISO 8601 UTC time."
    category = "personal_os"
    permission_level = "write"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "What to remind the user about"},
                "remind_at": {"type": "string", "description": "ISO 8601 datetime format for when to trigger the reminder. MUST be absolute time in UTC."},
            },
            "required": ["title", "remind_at"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                remind_at = parse_date(arguments["remind_at"])
                rem = Reminder(user_id=context.user_id, title=arguments["title"], remind_at=remind_at)
                db.add(rem)
                await db.commit()
                return ToolExecutionResult(success=True, tool_name=self.name, data={"id": rem.id, "status": "CREATED"})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class ProjectListTool(BaseTool):
    name = "project_list"
    description = "List active projects."
    category = "personal_os"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                r = await db.execute(select(Project).where(Project.user_id == context.user_id, Project.status == "ACTIVE"))
                projs = [{"id": p.id, "name": p.name} for p in r.scalars().all()]
                return ToolExecutionResult(success=True, tool_name=self.name, data={"projects": projs})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class NoteSearchTool(BaseTool):
    name = "note_search"
    description = "Semantic search for personal notes/ideas."
    category = "personal_os"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or sentence"}
            },
            "required": ["query"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                from app.interfaces.embedding_provider import EmbeddingProviderFactory
                provider = EmbeddingProviderFactory.get_provider()
                query = arguments["query"]
                
                try:
                    embedding = await provider.embed_query(query)
                    r = await db.execute(
                        select(Note).where(Note.user_id == context.user_id, Note.status == "ACTIVE", Note.embedding != None)
                        .order_by(Note.embedding.cosine_distance(embedding)).limit(3)
                    )
                    notes = r.scalars().all()
                except Exception:
                    # fallback
                    notes = []
                    
                if not notes:
                    r = await db.execute(select(Note).where(Note.user_id == context.user_id, Note.status == "ACTIVE", Note.content.ilike(f"%{query}%")).limit(3))
                    notes = r.scalars().all()
                    
                return ToolExecutionResult(success=True, tool_name=self.name, data={"notes": [{"id": n.id, "title": n.title, "content": n.content} for n in notes]})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})

class NoteCreateTool(BaseTool):
    name = "note_create"
    description = "Create a new personal note or idea."
    category = "personal_os"
    permission_level = "write"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title", "content"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        try:
            async with AsyncSessionLocal() as db:
                from app.interfaces.embedding_provider import EmbeddingProviderFactory
                provider = EmbeddingProviderFactory.get_provider()
                try:
                    embedding = await provider.embed_query(arguments["content"])
                except Exception:
                    embedding = None
                    
                note = Note(user_id=context.user_id, title=arguments["title"], content=arguments["content"], embedding=embedding)
                db.add(note)
                await db.commit()
                return ToolExecutionResult(success=True, tool_name=self.name, data={"id": note.id, "status": "CREATED"})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "ERROR", "message": str(e)})
