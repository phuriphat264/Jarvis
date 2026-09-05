import json
import logging
from typing import List, Optional, Dict, Any
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.interfaces.ai_provider import AIProviderFactory, AIResponse
from app.database.models.message import Message
from app.core_service.context_manager import ContextManager
from app.services.memory_search_service import MemorySearchService
from app.services.memory_extraction_service import MemoryExtractionService
from app.tools.registry import registry
from app.tools.executor import ToolExecutor
from app.interfaces.tool import ToolExecutionContext

logger = logging.getLogger("jarvis.core")

from app.world_model.context_aggregator import ContextAggregator
from app.world_model.situation_engine import SituationEngine

class JarvisCore:
    def __init__(self):
        self.ai = AIProviderFactory.get_provider()
        self.context_manager = ContextManager()
        self.memory_searcher = MemorySearchService()
        self.memory_extractor = MemoryExtractionService()
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        try:
            with open("prompts/jarvis_system.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning("System prompt file not found. Using default.")
            return "You are JARVIS, a helpful AI assistant."

    @retry(
        wait=wait_exponential(multiplier=settings.RETRY_DELAY, min=1, max=10),
        stop=stop_after_attempt(settings.MAX_RETRIES),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _call_ai_with_retry(self, messages: List[dict], tools: List[dict] = None) -> AIResponse:
        return await self.ai.generate_with_tools(messages, tools)

    async def process(self, request: str, history: List[Message], db: AsyncSession, user_id: int, background_tasks: BackgroundTasks = None, conversation_id: int = None, request_id: str = None, document_id: str = None) -> List[Dict[str, Any]]:
        """
        User Request -> Memory Search -> Context Manager -> AI Provider -> Tool Executor -> Loop -> Response -> Background Extraction
        Returns a list of messages to save to the database (assistant and tool messages).
        """
        try:
            logger.info("AI_REQUEST_STARTED")
            
            relevant_memories = []
            if settings.MEMORY_ENABLED:
                relevant_memories = await self.memory_searcher.search(db, user_id, request)
                
            # 1. Document Context (RAG)
            document_context_str = ""
            if document_id:
                from app.core_service.rag.retriever import RAGRetriever
                from app.core_service.rag.context_builder import RAGContextBuilder
                retriever = RAGRetriever(db)
                chunks = await retriever.search(user_id=user_id, query=request, document_id=document_id)
                document_context_str = RAGContextBuilder.build_context(chunks)
                
            # 2. Personal OS Context
            from app.core_service.personal_os_context import PersonalOSContextBuilder
            personal_os_context = await PersonalOSContextBuilder.build_context(db, user_id)
            if personal_os_context:
                document_context_str += "\n\n" + personal_os_context
                
            # 2.5 World Model Context (Phase 16)
            from app.world_model.context_aggregator import ContextAggregator
            from app.world_model.situation_engine import SituationEngine
            
            world_snapshot = await ContextAggregator.get_snapshot(user_id, db)
            situations = SituationEngine.detect_situations(world_snapshot)
            
            if situations:
                document_context_str += "\n\n--- CURRENT WORLD SITUATIONS ---\n"
                for s in situations:
                    document_context_str += f"- {s.type} (Severity: {s.severity})\n"
                    
            if world_snapshot.edge_state.get('nodes'):
                document_context_str += "\n\n--- EDGE STATE ---\n"
                document_context_str += f"Online Nodes: {world_snapshot.edge_state.get('online_count')}\n"

            # 2.6 Personalization Context (Phase 17)
            from app.personalization.adaptation_engine import AdaptationEngine
            personalization_ctx = await AdaptationEngine.get_context(user_id, db)
            if personalization_ctx:
                document_context_str += f"\n\n{personalization_ctx}"

            # 3. Agent Manager
            from app.core_service.agent.manager import agent_manager
            from app.core_service.agent.runtime import AgentRuntime
            
            agent_runtime = AgentRuntime(db, self.ai)
            am_result = await agent_manager.run(user_id, request, agent_runtime, conversation_id, request_id)
            
            if am_result.get("route") != "SIMPLE_CHAT":
                # Agent Manager executed tasks, inject results as context
                agent_res_str = "\n\n--- AGENT RESULTS ---\n"
                for res in am_result.get("results", []):
                    status = "SUCCESS" if res.get("success") else "FAILED"
                    agent_res_str += f"[{status}] {res.get('summary')} (Error: {res.get('error')})\n"
                document_context_str += agent_res_str
                
            messages = self.context_manager.build_context(
                self.system_prompt, 
                history, 
                request, 
                relevant_memories,
                document_context=document_context_str
            )
            
            tools_schema = registry.get_all_schemas() if settings.TOOLS_ENABLED else None
            
            loop_count = 0
            max_loops = settings.MAX_TOOL_CALLS_PER_REQUEST if settings.TOOLS_ENABLED else 0
            
            new_messages_to_save = []
            final_content = None
            
            while loop_count <= max_loops:
                ai_response = await self._call_ai_with_retry(messages, tools=tools_schema)
                
                # Check for tool calls
                if ai_response.tool_calls and loop_count < max_loops:
                    logger.info(f"LLM requested {len(ai_response.tool_calls)} tool calls.")
                    
                    # 1. Save assistant message with tool calls
                    assistant_msg = {
                        "role": "assistant",
                        "content": ai_response.content,
                        "tool_calls": ai_response.tool_calls
                    }
                    messages.append(assistant_msg)
                    new_messages_to_save.append(assistant_msg)
                    
                    # 2. Execute each tool call
                    for tc in ai_response.tool_calls:
                        tool_call_id = tc["id"]
                        tool_name = tc["function"]["name"]
                        
                        try:
                            arguments = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            arguments = {}
                            
                        # Execute
                        ctx = ToolExecutionContext(
                            user_id=user_id,
                            conversation_id=conversation_id,
                            request_id=request_id,
                            tool_call_id=tool_call_id
                        )
                        result = await ToolExecutor.execute(ctx, tool_name, arguments)
                        
                        # 3. Format result
                        result_content = json.dumps({
                            "success": result.success,
                            "data": result.data,
                            "error": result.error
                        }, ensure_ascii=False)
                        
                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": result_content
                        }
                        messages.append(tool_msg)
                        new_messages_to_save.append(tool_msg)
                        
                    loop_count += 1
                    continue # Loop back to AI
                    
                else:
                    # No tool calls, or max loops reached
                    final_content = ai_response.content
                    final_msg = {
                        "role": "assistant",
                        "content": final_content
                    }
                    messages.append(final_msg)
                    new_messages_to_save.append(final_msg)
                    break
            
            if background_tasks and conversation_id and settings.MEMORY_ENABLED:
                # Add the new messages to history for extraction context
                extraction_history = history.copy()
                extraction_history.append(Message(role="user", content=request))
                for nm in new_messages_to_save:
                    extraction_history.append(Message(
                        role=nm["role"], 
                        content=nm.get("content"),
                        tool_calls=nm.get("tool_calls"),
                        tool_name=nm.get("name")
                    ))
                
                # Keep only recent for extraction
                extraction_history = extraction_history[-10:] 
                background_tasks.add_task(self.memory_extractor.run_extraction_background, user_id, conversation_id, extraction_history)
                
            logger.info("AI_REQUEST_COMPLETED")
            return new_messages_to_save
            
        except Exception as e:
            logger.error(f"AI_REQUEST_FAILED: {str(e)}")
            return [{"role": "assistant", "content": "ขณะนี้ JARVIS ไม่สามารถเชื่อมต่อระบบได้ กรุณาลองใหม่อีกครั้ง"}]
