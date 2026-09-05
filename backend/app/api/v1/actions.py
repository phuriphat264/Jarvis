from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.integration import PendingAction
from app.database.models.activity_log import ActivityLog
from app.schemas.integration import PendingActionResponse
from app.core.dependencies import get_current_user
from app.tools.registry import registry
from app.interfaces.tool import ToolExecutionContext

router = APIRouter()

@router.get("/pending", response_model=List[PendingActionResponse])
async def list_pending_actions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PendingAction)
        .where(
            PendingAction.user_id == current_user.id,
            PendingAction.status == "PENDING"
        )
    )
    # We should also expire old ones, but ignoring for simplicity in read path
    return result.scalars().all()

@router.post("/{action_id}/confirm")
async def confirm_action(action_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PendingAction).where(PendingAction.id == action_id, PendingAction.user_id == current_user.id))
    action = result.scalars().first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    if action.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Action is {action.status}")
        
    if action.expires_at.tzinfo is None:
        action.expires_at = action.expires_at.replace(tzinfo=timezone.utc)
        
    if datetime.now(timezone.utc) > action.expires_at:
        action.status = "EXPIRED"
        await db.commit()
        raise HTTPException(status_code=400, detail="Action expired")
        
    # Execute the tool
    tool = registry.get_tool(action.tool_name)
    if not tool:
        action.status = "FAILED"
        await db.commit()
        raise HTTPException(status_code=400, detail="Tool not found")
        
    ctx = ToolExecutionContext(
        user_id=current_user.id,
        tool_call_id=f"pending_{action.id}"
    )
    
    # Bypass confirmation
    setattr(tool, "requires_confirmation", False)
    try:
        res = await tool.execute(ctx, action.arguments)
        action.status = "EXECUTED" if res.success else "FAILED"
    except Exception as e:
        action.status = "FAILED"
    finally:
        setattr(tool, "requires_confirmation", True)
        
    action.confirmed_at = datetime.now(timezone.utc)
    
    log = ActivityLog(user_id=current_user.id, action="EXTERNAL_ACTION_CONFIRMED", details={"action_id": action.id, "tool": action.tool_name})
    db.add(log)
    
    await db.commit()
    return {"success": True, "status": action.status}

@router.post("/{action_id}/reject")
async def reject_action(action_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PendingAction).where(PendingAction.id == action_id, PendingAction.user_id == current_user.id))
    action = result.scalars().first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    action.status = "REJECTED"
    
    log = ActivityLog(user_id=current_user.id, action="EXTERNAL_ACTION_REJECTED", details={"action_id": action.id})
    db.add(log)
    
    await db.commit()
    return {"success": True}
