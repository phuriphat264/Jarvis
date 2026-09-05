from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.interfaces.ai_provider import AIResponse

class AgentStepState(BaseModel):
    step_number: int
    action_type: str # THINK, TOOL_CALL, TOOL_RESULT, FINAL_ANSWER
    tool_name: Optional[str] = None
    status: str
    duration_ms: Optional[float] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentTaskState(BaseModel):
    task_id: int
    user_id: int
    conversation_id: Optional[int] = None
    request_id: Optional[str] = None
    status: str
    current_step: int
    max_steps: int
    final_result: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    steps: List[AgentStepState] = []

class BaseAgent:
    name: str
    
    async def step(self, task_state: AgentTaskState, context_messages: List[Dict[str, Any]]) -> AIResponse:
        """
        Executes one step of thinking or decision making based on the current context.
        Returns an AIResponse which could contain tool_calls or final content.
        """
        raise NotImplementedError
