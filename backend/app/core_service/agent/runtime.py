import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

from app.core.config import settings
from app.database.models.agent import AgentTask, AgentStep
from app.database.models.message import Message
from app.database.models.activity_log import ActivityLog
from app.interfaces.agent import AgentTaskState
from app.core_service.agent.general_agent import GeneralTaskAgent
from app.core_service.context_manager import ContextManager
from app.services.conversation_service import ConversationService
from app.tools.executor import ToolExecutor
from app.interfaces.tool import ToolExecutionContext

logger = logging.getLogger("jarvis.agent.runtime")

class AgentRuntime:
    def __init__(self, db: AsyncSession, agent=None):
        self.db = db
        self.agent = agent if agent else GeneralTaskAgent()
        self.context_manager = ContextManager()
        
    async def _get_task(self, task_id: int) -> Optional[AgentTask]:
        return await self.db.get(AgentTask, task_id)
        
    async def _log_step(self, task: AgentTask, action_type: str, status: str, tool_name: str = None, duration_ms: float = None, error: dict = None):
        step = AgentStep(
            task_id=task.id,
            step_number=task.current_step,
            action_type=action_type,
            tool_name=tool_name,
            status=status,
            duration_ms=duration_ms,
            error=error
        )
        self.db.add(step)
        await self.db.commit()
        
    async def run(self, task_id: int, user_request: str, system_prompt: str, history: List[Message], document_id: str = None):
        task = await self._get_task(task_id)
        if not task or task.status != "PENDING":
            return
            
        task.status = "RUNNING"
        task.started_at = func.now()
        await self.db.commit()
        
        logger.info(f"AGENT_TASK_STARTED: {task.id}")
        
        # Log to activity
        act_log = ActivityLog(user_id=task.user_id, action="AGENT_TASK_STARTED", details={"task_id": task.id})
        self.db.add(act_log)
        await self.db.commit()
        
        start_time = time.time()
        recent_tool_calls = [] # For no-progress detection
        
        try:
            document_context_str = ""
            if document_id:
                # User specifically requested this document
                from app.core_service.rag.retriever import RAGRetriever
                from app.core_service.rag.context_builder import RAGContextBuilder
                retriever = RAGRetriever(self.db)
                chunks = await retriever.search(user_id=task.user_id, query=user_request, document_id=document_id)
                document_context_str = RAGContextBuilder.build_context(chunks)
                
            context_messages = self.context_manager.build_context(
                system_prompt, 
                history, 
                user_request, 
                relevant_memories=[],
                document_context=document_context_str
            )
            
            while task.status == "RUNNING":
                # Check limits
                if task.current_step >= task.max_steps:
                    task.status = "LIMIT_REACHED"
                    task.error = {"message": "Max steps reached"}
                    break
                    
                if (time.time() - start_time) > settings.AGENT_TIMEOUT_SECONDS:
                    task.status = "TIMEOUT"
                    task.error = {"message": "Agent execution timed out"}
                    break
                    
                # Refresh task from DB to check for cancellation
                await self.db.refresh(task)
                if task.status == "CANCELLED":
                    break
                    
                task.current_step += 1
                await self.db.commit()
                
                # Agent step
                task_state = AgentTaskState(
                    task_id=task.id, user_id=task.user_id, conversation_id=task.conversation_id, 
                    request_id=task.request_id, status=task.status, current_step=task.current_step, max_steps=task.max_steps
                )
                
                step_start_time = time.time()
                ai_response = await self.agent.step(task_state, context_messages)
                
                # Process response
                if ai_response.tool_calls:
                    # Log THINK/TOOL_CALL
                    # We might have multiple tool calls in one step, process sequentially for simplicity in DB logging
                    for tc in ai_response.tool_calls:
                        tool_name = tc["function"]["name"]
                        arguments_str = tc["function"]["arguments"]
                        
                        # No-progress detection
                        call_sig = f"{tool_name}:{arguments_str}"
                        if recent_tool_calls.count(call_sig) >= 3:
                            task.status = "FAILED"
                            task.error = {"message": "No progress detected. Repeating identical tool calls."}
                            break
                        recent_tool_calls.append(call_sig)
                        if len(recent_tool_calls) > 5:
                            recent_tool_calls.pop(0)
                            
                        # Add assistant tool call to context
                        assistant_msg = {
                            "role": "assistant",
                            "content": ai_response.content or "",
                            "tool_calls": [tc] # Simplified to context
                        }
                        context_messages.append(assistant_msg)
                        
                        try:
                            arguments = json.loads(arguments_str)
                        except json.JSONDecodeError:
                            arguments = {}
                            
                        tool_ctx = ToolExecutionContext(
                            user_id=task.user_id,
                            conversation_id=task.conversation_id,
                            request_id=task.request_id,
                            tool_call_id=tc["id"]
                        )
                        
                        tool_start = time.time()
                        result = await ToolExecutor.execute(tool_ctx, tool_name, arguments)
                        tool_duration = (time.time() - tool_start) * 1000
                        
                        # Log step
                        await self._log_step(task, "TOOL_CALL", "COMPLETED" if result.success else "FAILED", tool_name, tool_duration, result.error)
                        
                        # Format result for context
                        result_content = json.dumps({
                            "success": result.success,
                            "data": result.data,
                            "error": result.error
                        }, ensure_ascii=False)
                        
                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": tool_name,
                            "content": result_content
                        }
                        context_messages.append(tool_msg)
                        
                else:
                    # Final Answer
                    task.final_result = ai_response.content
                    task.status = "COMPLETED"
                    step_duration = (time.time() - step_start_time) * 1000
                    await self._log_step(task, "FINAL_ANSWER", "COMPLETED", duration_ms=step_duration)
                    
                    # Log activity
                    act_log = ActivityLog(user_id=task.user_id, action="AGENT_TASK_COMPLETED", details={"task_id": task.id})
                    self.db.add(act_log)
                    break
                    
            # Loop ended
            if task.status not in ["COMPLETED", "CANCELLED"]:
                # If we broke out due to limit or error
                if task.status == "RUNNING":
                    task.status = "FAILED"
                act_log = ActivityLog(user_id=task.user_id, action=f"AGENT_TASK_{task.status}", details={"task_id": task.id})
                self.db.add(act_log)
                
            task.completed_at = func.now()
            await self.db.commit()
            
            # Save final message to conversation if successful
            if task.status == "COMPLETED" and task.conversation_id:
                await ConversationService.add_message(self.db, task.conversation_id, "user", user_request, task.request_id)
                await ConversationService.add_message(self.db, task.conversation_id, "assistant", task.final_result)
                
            logger.info(f"AGENT_TASK_FINISHED: {task.id} with status {task.status}")
            
        except Exception as e:
            logger.error(f"AGENT_TASK_ERROR: {task.id} - {str(e)}")
            task.status = "FAILED"
            task.error = {"message": str(e)}
            task.completed_at = func.now()
            
            act_log = ActivityLog(user_id=task.user_id, action="AGENT_TASK_FAILED", details={"task_id": task.id, "error": str(e)})
            self.db.add(act_log)
            await self.db.commit()
