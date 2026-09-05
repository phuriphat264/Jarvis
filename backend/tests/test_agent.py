import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock

from app.database.models.agent import AgentTask, AgentStep
from app.core_service.agent.runtime import AgentRuntime
from app.interfaces.ai_provider import AIResponse

@pytest.fixture
def mock_db():
    db = AsyncMock()
    # Mocks for DB operations can be configured here
    return db

@pytest.mark.asyncio
async def test_agent_runtime_no_progress_detection(mock_db):
    runtime = AgentRuntime(mock_db)
    
    # Create a mock task
    task = AgentTask(id=1, status="PENDING", user_id=1, current_step=0, max_steps=10)
    
    runtime._get_task = AsyncMock(return_value=task)
    runtime._log_step = AsyncMock()
    
    # Mock agent to constantly return the same tool call
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "calculator",
            "arguments": '{"expression": "1 + 1"}'
        }
    }
    
    runtime.agent.step = AsyncMock(return_value=AIResponse(content=None, tool_calls=[tool_call]))
    
    # Mock context manager
    runtime.context_manager.build_context = MagicMock(return_value=[])
    
    # We don't actually want to call ToolExecutor, let's mock it
    from app.tools.executor import ToolExecutor
    from app.interfaces.tool import ToolExecutionResult
    ToolExecutor.execute = AsyncMock(return_value=ToolExecutionResult(success=True, tool_name="calculator", data={"result": 2}))
    
    await runtime.run(task_id=1, user_request="Do it", system_prompt="", history=[])
    
    assert task.status == "FAILED"
    assert "No progress detected" in task.error["message"]
    
@pytest.mark.asyncio
async def test_agent_runtime_max_steps(mock_db):
    runtime = AgentRuntime(mock_db)
    
    # Create a mock task
    task = AgentTask(id=2, status="PENDING", user_id=1, current_step=0, max_steps=2)
    
    runtime._get_task = AsyncMock(return_value=task)
    runtime._log_step = AsyncMock()
    
    # Mock agent to return unique tool calls so it doesn't trigger no-progress
    call_counter = 0
    async def mock_step(*args, **kwargs):
        nonlocal call_counter
        call_counter += 1
        tool_call = {
            "id": f"call_{call_counter}",
            "type": "function",
            "function": {
                "name": "calculator",
                "arguments": f'{{"expression": "{call_counter} + 1"}}'
            }
        }
        return AIResponse(content=None, tool_calls=[tool_call])
        
    runtime.agent.step = mock_step
    runtime.context_manager.build_context = MagicMock(return_value=[])
    
    from app.tools.executor import ToolExecutor
    from app.interfaces.tool import ToolExecutionResult
    ToolExecutor.execute = AsyncMock(return_value=ToolExecutionResult(success=True, tool_name="calculator", data={"result": 2}))
    
    await runtime.run(task_id=2, user_request="Do it", system_prompt="", history=[])
    
    assert task.status == "LIMIT_REACHED"
    assert "Max steps reached" in task.error["message"]
    assert task.current_step == 2
