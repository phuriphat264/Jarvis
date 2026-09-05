from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.database.session import get_db
from app.database.models.user import User
from app.database.models.agent import AgentTask, AgentStep
from app.database.models.message import Message
from app.core.dependencies import get_current_user
from app.core_service.agent.runtime import AgentRuntime
from app.schemas.schemas import APIResponse
from app.core.config import settings

router = APIRouter()

class TaskCreateRequest(BaseModel):
    request: str
    conversation_id: Optional[int] = None
    client_request_id: Optional[str] = None
    agent_type: Optional[str] = "general" # 'general' or 'research'
    document_id: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: int
    status: str
    current_step: int
    max_steps: int
    final_result: Optional[str] = None
    error: Optional[dict] = None
    steps: List[dict] = []

@router.post("/tasks", response_model=APIResponse)
async def create_agent_task(
    req: TaskCreateRequest, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Idempotency check
    req_id = req.client_request_id or str(uuid.uuid4())
    if req.client_request_id:
        result = await db.execute(select(AgentTask).where(AgentTask.request_id == req_id))
        existing = result.scalars().first()
        if existing:
            return APIResponse(success=True, data={"task_id": existing.id})
            
    # Load history if conversation_id provided
    history = []
    if req.conversation_id:
        h_result = await db.execute(select(Message).where(Message.conversation_id == req.conversation_id).order_by(Message.sequence))
        history = h_result.scalars().all()
        
    # Create Task
    task = AgentTask(
        user_id=current_user.id,
        conversation_id=req.conversation_id,
        request_id=req_id,
        status="PENDING",
        max_steps=settings.MAX_AGENT_STEPS
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Load system prompt
    try:
        with open("prompts/jarvis_system.txt", "r") as f:
            system_prompt = f.read().strip()
    except:
        system_prompt = "You are JARVIS, a helpful AI assistant."
    
    # Select Agent
    if req.agent_type == "research":
        from app.core_service.agent.research_agent import ResearchAgent
        agent = ResearchAgent()
    else:
        from app.core_service.agent.general_agent import GeneralTaskAgent
        agent = GeneralTaskAgent()
        
    # Run in background
    runtime = AgentRuntime(db, agent=agent)
    background_tasks.add_task(runtime.run, task.id, req.request, system_prompt, history, req.document_id)
    
    return APIResponse(success=True, data={"task_id": task.id})

@router.get("/tasks/{task_id}", response_model=APIResponse)
async def get_agent_task(
    task_id: int, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AgentTask).options(selectinload(AgentTask.steps)).where(AgentTask.id == task_id, AgentTask.user_id == current_user.id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    steps_out = []
    for s in task.steps:
        steps_out.append({
            "step_number": s.step_number,
            "action_type": s.action_type,
            "tool_name": s.tool_name,
            "status": s.status,
            "duration_ms": s.duration_ms,
            "error": s.error
        })
        
    data = {
        "task_id": task.id,
        "status": task.status,
        "current_step": task.current_step,
        "max_steps": task.max_steps,
        "final_result": task.final_result,
        "error": task.error,
        "steps": steps_out
    }
    return APIResponse(success=True, data=data)

@router.post("/tasks/{task_id}/cancel", response_model=APIResponse)
async def cancel_agent_task(
    task_id: int, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == current_user.id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status in ["PENDING", "RUNNING", "WAITING_CONFIRMATION"]:
        task.status = "CANCELLED"
        await db.commit()
        return APIResponse(success=True, data={"status": "CANCELLED"})
    else:
        return APIResponse(success=False, error={"message": f"Cannot cancel task in state {task.status}"})

@router.get("/runs")
async def get_agent_runs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.database.models.agent_manager import AgentManagerRun
    result = await db.execute(select(AgentManagerRun).where(AgentManagerRun.user_id == current_user.id).order_by(AgentManagerRun.created_at.desc()).limit(20))
    runs = result.scalars().all()
    return APIResponse(success=True, data=[{
        "id": r.id,
        "request": r.input_text,
        "route_type": r.route_type,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None
    } for r in runs])

@router.get("/runs/{run_id}")
async def get_agent_run(run_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.database.models.agent_manager import AgentManagerRun
    result = await db.execute(select(AgentManagerRun).where(AgentManagerRun.id == run_id, AgentManagerRun.user_id == current_user.id))
    r = result.scalars().first()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return APIResponse(success=True, data={
        "id": r.id,
        "request": r.input_text,
        "route_type": r.route_type,
        "status": r.status,
        "plan": r.plan,
        "final_result": r.final_result,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None
    })

@router.get("/registry")
async def get_agent_registry():
    from app.core_service.agent.registry import agent_registry
    return APIResponse(success=True, data=agent_registry.get_agent_metadata())
