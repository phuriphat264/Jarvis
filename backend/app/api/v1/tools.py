from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.database.models.user import User
from app.core.dependencies import get_current_user
from app.tools.registry import registry
from app.schemas.schemas import APIResponse

router = APIRouter()

@router.get("/", response_model=APIResponse)
async def get_tools(current_user: User = Depends(get_current_user)):
    """
    Returns the list of available tools.
    """
    tools = registry.list_tools()
    tool_list = []
    for t in tools:
        tool_list.append({
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "permission_level": t.permission_level
        })
        
    return APIResponse(success=True, data={"tools": tool_list})
