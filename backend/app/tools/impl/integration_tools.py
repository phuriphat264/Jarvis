from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult
from app.database.session import AsyncSessionLocal
from sqlalchemy.future import select
from app.database.models.integration import IntegrationConnection

# In a real app we'd fetch the connection and use the access token
async def check_connection(db, user_id: int, provider: str):
    result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.user_id == user_id, IntegrationConnection.provider == provider, IntegrationConnection.status == "CONNECTED"))
    return result.scalars().first()

class GoogleCalendarListTool(BaseTool):
    name = "google_calendar_list"
    description = "List events from Google Calendar."
    category = "integration"
    permission_level = "read"
    requires_confirmation = False

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        async with AsyncSessionLocal() as db:
            if not await check_connection(db, context.user_id, "google_calendar"):
                return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_CONNECTED", "message": "Google Calendar is not connected."})
        return ToolExecutionResult(success=True, tool_name=self.name, data={"events": [{"id": "mock1", "summary": "Sync meeting", "start": "2026-09-06T10:00:00Z"}]})

class GoogleCalendarCreateTool(BaseTool):
    name = "google_calendar_create"
    description = "Create an event in Google Calendar."
    category = "integration"
    permission_level = "write"
    requires_confirmation = True # Modifying external state

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"}
            },
            "required": ["summary", "start_time", "end_time"]
        }

    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        async with AsyncSessionLocal() as db:
            if not await check_connection(db, context.user_id, "google_calendar"):
                return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_CONNECTED", "message": "Google Calendar is not connected."})
        return ToolExecutionResult(success=True, tool_name=self.name, data={"id": "mock_new", "status": "CREATED"})

class GmailSearchTool(BaseTool):
    name = "gmail_search"
    description = "Search emails in Gmail."
    category = "integration"
    permission_level = "read"
    requires_confirmation = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query"}
            },
            "required": ["query"]
        }

    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        async with AsyncSessionLocal() as db:
            if not await check_connection(db, context.user_id, "gmail"):
                return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_CONNECTED", "message": "Gmail is not connected."})
        return ToolExecutionResult(success=True, tool_name=self.name, data={"emails": [{"id": "msg1", "subject": "Project Update", "snippet": "Here is the latest..."}]})

class LineSendMessageTool(BaseTool):
    name = "line_send_message"
    description = "Send a message via LINE."
    category = "integration"
    permission_level = "write"
    requires_confirmation = True

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }

    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        async with AsyncSessionLocal() as db:
            if not await check_connection(db, context.user_id, "line"):
                return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_CONNECTED", "message": "LINE is not connected."})
        return ToolExecutionResult(success=True, tool_name=self.name, data={"status": "SENT"})

class TelegramSendMessageTool(BaseTool):
    name = "telegram_send_message"
    description = "Send a message via Telegram."
    category = "integration"
    permission_level = "write"
    requires_confirmation = True

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }

    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        async with AsyncSessionLocal() as db:
            if not await check_connection(db, context.user_id, "telegram"):
                return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "NOT_CONNECTED", "message": "Telegram is not connected."})
        return ToolExecutionResult(success=True, tool_name=self.name, data={"status": "SENT"})

class WebhookSendTool(BaseTool):
    name = "webhook_send"
    description = "Send a webhook payload to a pre-registered destination."
    category = "integration"
    permission_level = "write"
    requires_confirmation = True # Modifying external state

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "destination_id": {"type": "string", "description": "The registered ID of the webhook (NOT an arbitrary URL)"},
                "payload": {"type": "object"}
            },
            "required": ["destination_id", "payload"]
        }

    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        # In reality, this would check a registered_webhooks table.
        return ToolExecutionResult(success=True, tool_name=self.name, data={"status": "SENT"})
