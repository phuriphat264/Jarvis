from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AgentResult(BaseModel):
    success: bool
    agent_name: str
    task_id: str
    summary: str
    structured_data: Optional[Dict[str, Any]] = None
    citations: Optional[List[str]] = None
    artifacts: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class BaseSpecialistAgent:
    name: str
    description: str
    purpose: str
    capabilities: List[str]
    allowed_tools: List[str]
    allowed_permissions: List[str]
    timeout: int = 60
    max_steps: int = 6
    enabled: bool = True

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "capabilities": self.capabilities,
            "allowed_tools": self.allowed_tools,
            "enabled": self.enabled
        }

    def can_handle(self, task: str) -> bool:
        """Returns True if this agent is suited for the task."""
        raise NotImplementedError

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        """Returns the system prompt for the agent's LLM context."""
        raise NotImplementedError

    async def execute(self, task_context: Dict[str, Any], agent_runtime) -> AgentResult:
        """Executes the task using the provided agent runtime."""
        raise NotImplementedError

    def validate_output(self, result: AgentResult) -> bool:
        """Validates if the result meets the agent's schema requirements."""
        return True
