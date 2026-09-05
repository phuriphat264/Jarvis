from typing import Dict, Any, Optional
from pydantic import BaseModel

class ToolExecutionContext(BaseModel):
    user_id: int
    conversation_id: Optional[int] = None
    request_id: Optional[str] = None
    tool_call_id: str
    
class ToolExecutionResult(BaseModel):
    success: bool
    tool_name: str
    data: Optional[Any] = None
    error: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseTool:
    name: str
    description: str
    category: str = "general"
    permission_level: str = "read" # read, write, external
    
    def get_schema(self) -> Dict[str, Any]:
        """Returns the JSON Schema for the tool arguments"""
        raise NotImplementedError
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """Executes the tool with given arguments and context"""
        raise NotImplementedError
