from typing import Dict, Any, List
from datetime import datetime
from app.interfaces.specialist_agent import BaseSpecialistAgent, AgentResult

class GenericAgentWrapper(BaseSpecialistAgent):
    """A wrapper that implements the standard execute pattern for a specialist agent"""
    async def execute(self, task_context: Dict[str, Any], agent_runtime) -> AgentResult:
        # Create an AgentTask manually via agent_runtime's DB
        # Run it using the runtime
        import time
        from sqlalchemy.sql import func
        from app.database.models.agent import AgentTask
        
        db = agent_runtime.db
        user_id = task_context.get("user_id")
        conversation_id = task_context.get("conversation_id")
        request_id = task_context.get("request_id")
        run_id = task_context.get("agent_manager_run_id")
        task_objective = task_context.get("objective")
        
        agent_task = AgentTask(
            user_id=user_id,
            conversation_id=conversation_id,
            request_id=request_id,
            agent_manager_run_id=run_id,
            agent_name=self.name,
            max_steps=self.max_steps,
            status="PENDING"
        )
        db.add(agent_task)
        await db.commit()
        await db.refresh(agent_task)
        
        system_prompt = self.get_system_prompt(task_context)
        history = task_context.get("history", [])
        
        start = datetime.now()
        await agent_runtime.run(agent_task.id, task_objective, system_prompt, history)
        
        await db.refresh(agent_task)
        
        success = agent_task.status == "COMPLETED"
        return AgentResult(
            success=success,
            agent_name=self.name,
            task_id=str(agent_task.id),
            summary=agent_task.final_result if success else f"Failed with status: {agent_task.status}",
            error=str(agent_task.error) if not success else None,
            started_at=start.isoformat(),
            completed_at=datetime.now().isoformat()
        )

class PersonalOSAgent(GenericAgentWrapper):
    name = "personal_os"
    description = "Manages tasks, projects, goals, notes, reminders, and calendar."
    purpose = "Execute actions and queries related to the user's personal organization."
    capabilities = ["task_management", "calendar_sync", "note_taking"]
    allowed_tools = ["dashboard_get", "task_create", "task_list", "task_update", "task_complete", "reminder_create", "project_list", "note_search", "note_create"]
    allowed_permissions = ["READ", "WRITE"]
    
    def can_handle(self, task: str) -> bool:
        keywords = ["task", "งาน", "โปรเจกต์", "project", "note", "จด", "เตือน", "reminder", "calendar", "ปฏิทิน", "เป้าหมาย", "goal"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Personal OS Agent. Manage the user's tasks, notes, and calendar. Objective: {task_context.get('objective')}"

class ResearchAgent(GenericAgentWrapper):
    name = "research"
    description = "Searches the web, compares sources, and synthesizes external information."
    purpose = "Provide accurate external information through web search and fetch."
    capabilities = ["web_search", "web_fetch", "synthesis"]
    allowed_tools = ["web_search", "web_fetch"]
    allowed_permissions = ["READ"]
    
    def can_handle(self, task: str) -> bool:
        keywords = ["หาข้อมูล", "ค้นหา", "search", "research", "อินเทอร์เน็ต", "internet"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Research Agent. Use web tools to answer queries. Objective: {task_context.get('objective')}"

class DocumentAgent(GenericAgentWrapper):
    name = "document"
    description = "Extracts and synthesizes information from uploaded documents."
    purpose = "Answer questions based on private files and PDFs using RAG."
    capabilities = ["rag", "document_search", "summarization"]
    allowed_tools = ["file_search"]
    allowed_permissions = ["READ"]
    
    def can_handle(self, task: str) -> bool:
        keywords = ["เอกสาร", "document", "pdf", "file", "ไฟล์", "สรุป"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Document Agent. Use file search tools to extract information. Objective: {task_context.get('objective')}"

class VisionAgent(GenericAgentWrapper):
    name = "vision"
    description = "Analyzes images and extracts text (OCR)."
    purpose = "Process visual input and explain images."
    capabilities = ["ocr", "image_analysis"]
    allowed_tools = ["vision_analyze"]
    allowed_permissions = ["READ"]
    
    def can_handle(self, task: str) -> bool:
        keywords = ["ภาพ", "รูป", "image", "picture", "ocr", "อ่านข้อความจากภาพ"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Vision Agent. Analyze images carefully. Objective: {task_context.get('objective')}"

class PlanningAgent(GenericAgentWrapper):
    name = "planning"
    description = "Breaks complex tasks into manageable steps and structured plans."
    purpose = "Create logical execution plans or schedules."
    capabilities = ["planning", "scheduling"]
    allowed_tools = ["task_create", "project_list"] # Can create tasks for the plan
    allowed_permissions = ["READ", "WRITE"]
    
    def can_handle(self, task: str) -> bool:
        keywords = ["วางแผน", "plan", "schedule", "จัดตาราง"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Planning Agent. Structure complex plans and create tasks if asked. Objective: {task_context.get('objective')}"

class CommunicationAgent(GenericAgentWrapper):
    name = "communication"
    description = "Manages external messaging via Gmail, LINE, and Telegram."
    purpose = "Send and read messages safely."
    capabilities = ["email", "messaging"]
    allowed_tools = ["gmail_search", "line_send_message", "telegram_send_message"]
    allowed_permissions = ["READ", "WRITE_EXTERNAL"] # Subject to confirmation
    
    def can_handle(self, task: str) -> bool:
        keywords = ["ส่งข้อความ", "email", "gmail", "เมล", "อีเมล", "line", "ไลน์", "telegram"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Communication Agent. Prepare external messages securely. Objective: {task_context.get('objective')}"

class CodingAgent(GenericAgentWrapper):
    name = "coding"
    description = "Analyzes and generates code."
    purpose = "Assist with programming tasks in an isolated workspace."
    capabilities = ["code_analysis", "generation"]
    allowed_tools = []
    allowed_permissions = ["READ"]
    enabled = False # Disabled by default as requested
    
    def can_handle(self, task: str) -> bool:
        keywords = ["code", "โค้ด", "เขียนโปรแกรม", "debug", "bug", "script"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the Coding Agent. Assist with software development safely. Objective: {task_context.get('objective')}"

class IoTAgent(GenericAgentWrapper):
    name = "iot"
    description = "Controls and monitors smart home devices safely."
    purpose = "Execute validated commands on physical IoT devices."
    capabilities = ["device_control", "sensor_reading"]
    allowed_tools = ["iot_device_list", "iot_device_status", "iot_device_control"]
    allowed_permissions = ["READ", "WRITE"]
    
    def can_handle(self, task: str) -> bool:
        keywords = ["ไฟ", "ปลั๊ก", "light", "plug", "เปิด", "ปิด", "อุณหภูมิ", "แอร์", "พัดลม", "ห้อง"]
        return any(k in task.lower() for k in keywords)

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are the IoT Agent. Control devices safely based on exact requests. Objective: {task_context.get('objective')}"

class GeneralAgent(GenericAgentWrapper):
    name = "general"
    description = "General reasoning and simple chat."
    purpose = "Handle queries that don't need specialization."
    capabilities = ["reasoning"]
    allowed_tools = ["datetime_tool", "calculator"]
    allowed_permissions = ["READ"]
    
    def can_handle(self, task: str) -> bool:
        return True

    def get_system_prompt(self, task_context: Dict[str, Any]) -> str:
        return f"You are JARVIS's General Assistant. Handle basic queries. Objective: {task_context.get('objective')}"
