import pytest
from app.core_service.agent.registry import agent_registry
from app.core_service.agent.router import AgentRouter

def test_agent_registry():
    agents = agent_registry.get_enabled_agents()
    assert len(agents) > 0
    names = [a.name for a in agents]
    assert "general" in names
    assert "personal_os" in names
    assert "research" in names
    assert "document" in names
    assert "vision" in names
    assert "planning" in names
    assert "communication" in names
    
    # Coding agent should exist but might be disabled by default based on enabled prop
    coding_agent = agent_registry.get_agent("coding")
    assert coding_agent is not None
    assert coding_agent.enabled is False

def test_agent_router_classification():
    # Multi-agent
    assert AgentRouter.classify_request("วิเคราะห์ PDF นี้ แล้วเปรียบเทียบกับข้อมูลล่าสุดจากเว็บ พร้อมทั้งสรุปมาให้ด้วย") == "MULTI_AGENT"
    
    # Planning
    assert AgentRouter.classify_request("ช่วยวางแผน project นี้ให้หน่อย") == "PLANNING"
    
    # Communication
    assert AgentRouter.classify_request("ส่งไลน์บอกแม่หน่อย") == "COMMUNICATION"
    
    # Personal OS
    assert AgentRouter.classify_request("พรุ่งนี้มีงานอะไรบ้าง") == "PERSONAL_OS"
    
    # Research
    assert AgentRouter.classify_request("หาข้อมูล AI ล่าสุด") == "RESEARCH"
    
    # Document
    assert AgentRouter.classify_request("สรุปไฟล์นี้") == "DOCUMENT"
    
    # Coding
    assert AgentRouter.classify_request("ช่วย debug code นี้หน่อย") == "CODING"
    
    # General (fallback)
    assert AgentRouter.classify_request("สวัสดี") == "SIMPLE_CHAT"

def test_agent_manager_limits():
    # Just asserting configs are present
    from app.core.config import settings
    assert hasattr(settings, "MAX_AGENT_RUNTIME_SECONDS")
    assert hasattr(settings, "MAX_AGENT_STEPS")
