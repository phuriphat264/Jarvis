import time
import logging
from typing import Dict, Any
from app.interfaces.tool import ToolExecutionContext, ToolExecutionResult
from app.tools.registry import registry
from app.core.config import settings

logger = logging.getLogger("jarvis.tool_executor")

class ToolExecutor:
    @staticmethod
    async def execute(context: ToolExecutionContext, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        if not settings.TOOLS_ENABLED:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error={"code": "TOOLS_DISABLED", "message": "Tool system is disabled globally."}
            )
            
        tool = registry.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error={"code": "TOOL_NOT_FOUND", "message": f"Tool '{tool_name}' not found."}
            )
            
        start_time = time.time()
        logger.info(f"TOOL_CALL_STARTED: {tool_name} by user {context.user_id}")
        
        try:
            # Check for explicit confirmation requirement
            if getattr(tool, "requires_confirmation", False):
                from app.database.session import AsyncSessionLocal
                from app.database.models.integration import PendingAction
                from datetime import datetime, timezone, timedelta
                import json
                
                async with AsyncSessionLocal() as db:
                    pending = PendingAction(
                        user_id=context.user_id,
                        tool_name=tool_name,
                        arguments=arguments,
                        description=f"Action requires confirmation: {tool.description}",
                        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
                    )
                    db.add(pending)
                    await db.commit()
                    
                    return ToolExecutionResult(
                        success=False, # It didn't execute yet
                        tool_name=tool_name,
                        error={"code": "CONFIRMATION_REQUIRED", "message": f"Please ask the user to confirm this action. Pending Action ID: {pending.id}"}
                    )
            
            # Execute normally
            result = await tool.execute(context, arguments)
            
        except Exception as e:
            logger.error(f"TOOL_CALL_FAILED: {tool_name}, Error: {str(e)}")
            result = ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error={"code": "INTERNAL_ERROR", "message": str(e)}
            )
            
        latency = (time.time() - start_time) * 1000
        if result.metadata is None:
            result.metadata = {}
        result.metadata["latency_ms"] = latency
        
        status = "COMPLETED" if result.success else "FAILED"
        logger.info(f"TOOL_CALL_{status}: {tool_name} in {latency:.2f}ms")
        
        return result
