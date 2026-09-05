from typing import List, Dict, Any
from app.interfaces.agent import BaseAgent, AgentTaskState
from app.interfaces.ai_provider import AIProviderFactory, AIResponse
from app.tools.registry import registry
from app.core.config import settings
import logging

logger = logging.getLogger("jarvis.agent.general")

class GeneralTaskAgent(BaseAgent):
    name = "GeneralTaskAgent"
    
    def __init__(self):
        self.ai = AIProviderFactory.get_provider()
        
    async def step(self, task_state: AgentTaskState, context_messages: List[Dict[str, Any]]) -> AIResponse:
        # The AI needs to see available tools
        tools_schema = registry.get_all_schemas() if settings.TOOLS_ENABLED else None
        
        # We also might want to append a small system prompt hint for the agent behavior
        agent_system_msg = {
            "role": "system",
            "content": f"You are JARVIS Agent. You are performing a bounded task. Step: {task_state.current_step}/{task_state.max_steps}. Use tools to make progress. Output your final answer when done."
        }
        
        # Inject the agent system msg at the beginning, right after the main system prompt.
        messages = context_messages.copy()
        if len(messages) > 0 and messages[0]["role"] == "system":
            messages.insert(1, agent_system_msg)
        else:
            messages.insert(0, agent_system_msg)
            
        logger.info(f"[{self.name}] Calling AI Provider for step {task_state.current_step}")
        response = await self.ai.generate_with_tools(messages, tools=tools_schema)
        
        return response
