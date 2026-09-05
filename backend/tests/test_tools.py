import pytest
import json
from app.interfaces.tool import ToolExecutionContext
from app.tools.registry import registry
from app.tools.executor import ToolExecutor
from app.tools.impl.calculator import CalculatorTool
from app.tools.impl.datetime_tool import DateTimeTool
from app.tools.impl.mock_tool import MockTool

@pytest.fixture
def dummy_context():
    return ToolExecutionContext(user_id=1, tool_call_id="call_123")

@pytest.mark.asyncio
async def test_registry():
    # Tools should already be registered on import of registry module
    assert registry.has_tool("calculator")
    assert registry.has_tool("mock_tool")
    
    schemas = registry.get_all_schemas()
    assert len(schemas) >= 4
    
@pytest.mark.asyncio
async def test_calculator(dummy_context):
    calc = registry.get_tool("calculator")
    
    # Valid
    res = await calc.execute(dummy_context, {"expression": "25 * 8"})
    assert res.success
    assert res.data["result"] == 200
    
    # Precedence
    res = await calc.execute(dummy_context, {"expression": "(10 + 5) / 3"})
    assert res.success
    assert res.data["result"] == 5.0
    
    # Invalid op
    res = await calc.execute(dummy_context, {"expression": "10 ** 1000"})
    assert not res.success
    
    res = await calc.execute(dummy_context, {"expression": "1 / 0"})
    assert not res.success
    
    # Code execution prevention
    res = await calc.execute(dummy_context, {"expression": "__import__('os').system('ls')"})
    assert not res.success
    
@pytest.mark.asyncio
async def test_datetime(dummy_context):
    dt = registry.get_tool("datetime")
    
    res = await dt.execute(dummy_context, {"timezone": "Asia/Tokyo"})
    assert res.success
    assert "datetime" in res.data
    
    res = await dt.execute(dummy_context, {"timezone": "Invalid/Timezone"})
    assert not res.success

@pytest.mark.asyncio
async def test_executor(dummy_context):
    # Executor wrapper test
    res = await ToolExecutor.execute(dummy_context, "calculator", {"expression": "2 + 2"})
    assert res.success
    assert res.data["result"] == 4
    assert res.metadata["latency_ms"] >= 0
    
    # Unknown tool
    res = await ToolExecutor.execute(dummy_context, "unknown", {})
    assert not res.success
    assert res.error["code"] == "TOOL_NOT_FOUND"
