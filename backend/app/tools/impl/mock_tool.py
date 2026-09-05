from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult

class MockTool(BaseTool):
    name = "mock_tool"
    description = "A mock tool for testing purposes."
    category = "test"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_string": {
                    "type": "string",
                    "description": "Any input string."
                }
            },
            "required": ["input_string"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        input_string = arguments.get("input_string", "")
        if input_string == "error":
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "MOCK_ERROR", "message": "Triggered mock error."})
        return ToolExecutionResult(success=True, tool_name=self.name, data={"result": f"Mock executed with: {input_string}"})
