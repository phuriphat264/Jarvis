from app.core_service.agent.registry import agent_registry
from app.core_service.agent.agents.specialists import (
    PersonalOSAgent, ResearchAgent, DocumentAgent, VisionAgent,
    PlanningAgent, CommunicationAgent, CodingAgent, GeneralAgent, IoTAgent
)

# Initialize registry
agent_registry.register(PersonalOSAgent())
agent_registry.register(ResearchAgent())
agent_registry.register(DocumentAgent())
agent_registry.register(VisionAgent())
agent_registry.register(PlanningAgent())
agent_registry.register(CommunicationAgent())
agent_registry.register(CodingAgent())
agent_registry.register(IoTAgent())
agent_registry.register(GeneralAgent())

class AgentRouter:
    @staticmethod
    def classify_request(request: str) -> str:
        req_lower = request.lower()
        
        # Simple heuristics for classification
        if any(w in req_lower for w in ["เปรียบเทียบ", "แล้ว", "จากนั้น", "พร้อมทั้ง"]) and len(req_lower.split()) > 10:
            return "MULTI_AGENT"
            
        # Match single specialists in priority order
        if PlanningAgent().can_handle(request): return "PLANNING"
        if CommunicationAgent().can_handle(request): return "COMMUNICATION"
        if CodingAgent().can_handle(request): return "CODING"
        if IoTAgent().can_handle(request): return "IOT"
        if DocumentAgent().can_handle(request): return "DOCUMENT"
        if VisionAgent().can_handle(request): return "VISION"
        if ResearchAgent().can_handle(request): return "RESEARCH"
        if PersonalOSAgent().can_handle(request): return "PERSONAL_OS"
        
        return "SIMPLE_CHAT"
