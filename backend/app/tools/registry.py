from typing import Dict, List, Any, Optional
from app.interfaces.tool import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        
    def unregister(self, tool_name: str) -> None:
        if tool_name in self._tools:
            del self._tools[tool_name]
            
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        return self._tools.get(tool_name)
        
    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools
        
    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())
        
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_schema()
                }
            })
        return schemas

# Singleton registry
registry = ToolRegistry()

# Register default tools
from app.tools.impl.calculator import CalculatorTool
from app.tools.impl.datetime_tool import DateTimeTool
from app.tools.impl.http_get import HttpGetTool
from app.tools.impl.mock_tool import MockTool
from app.tools.impl.web_search import WebSearchTool
from app.tools.impl.web_fetch import WebFetchTool
from app.tools.impl.file_search import FileSearchTool
from app.tools.impl.vision_analyze import VisionAnalyzeTool
from app.tools.impl.personal_os_tools import (
    DashboardGetTool, TaskCreateTool, TaskListTool, TaskUpdateTool, TaskCompleteTool,
    ReminderCreateTool, ProjectListTool, NoteSearchTool, NoteCreateTool
)

registry.register(CalculatorTool())
registry.register(DateTimeTool())
registry.register(HttpGetTool())
registry.register(MockTool())
registry.register(WebSearchTool())
registry.register(WebFetchTool())
registry.register(FileSearchTool())
registry.register(VisionAnalyzeTool())

# Personal OS Tools
registry.register(DashboardGetTool())
registry.register(TaskCreateTool())
registry.register(TaskListTool())
registry.register(TaskUpdateTool())
registry.register(TaskCompleteTool())
registry.register(ReminderCreateTool())
registry.register(ProjectListTool())
registry.register(NoteSearchTool())
registry.register(NoteCreateTool())

# Integration Tools
from app.tools.impl.integration_tools import (
    GoogleCalendarListTool, GoogleCalendarCreateTool,
    GmailSearchTool, LineSendMessageTool, TelegramSendMessageTool, WebhookSendTool
)
registry.register(GoogleCalendarListTool())
registry.register(GoogleCalendarCreateTool())
registry.register(GmailSearchTool())
registry.register(LineSendMessageTool())
registry.register(TelegramSendMessageTool())
registry.register(WebhookSendTool())

# IoT Tools
from app.tools.impl.iot_tools import IoTDeviceListTool, IoTDeviceControlTool, IoTDeviceStatusTool
registry.register(IoTDeviceListTool())
registry.register(IoTDeviceControlTool())
registry.register(IoTDeviceStatusTool())
