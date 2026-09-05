import pytest
import asyncio
from app.tools.impl.web_fetch import WebFetchTool
from app.tools.impl.web_search import WebSearchTool
from app.interfaces.tool import ToolExecutionContext

@pytest.mark.asyncio
async def test_web_fetch_ssrf_protection():
    tool = WebFetchTool()
    
    # Test valid
    assert tool._is_safe_url("https://www.google.com") == True
    
    # Test localhost
    assert tool._is_safe_url("http://localhost:8080") == False
    assert tool._is_safe_url("http://127.0.0.1") == False
    
    # Test private IPs
    assert tool._is_safe_url("http://192.168.1.1") == False
    assert tool._is_safe_url("http://10.0.0.1") == False
    
    # Test cloud metadata
    assert tool._is_safe_url("http://169.254.169.254/latest/meta-data") == False
    
    # Test invalid protocols
    assert tool._is_safe_url("file:///etc/passwd") == False
    assert tool._is_safe_url("ftp://example.com") == False

def test_web_fetch_html_extraction():
    tool = WebFetchTool()
    html = \"\"\"
    <html>
        <head><title>Test Page</title></head>
        <body>
            <header>Header</header>
            <nav>Menu</nav>
            <script>alert(1);</script>
            <style>body { color: red; }</style>
            <h1>Main Content</h1>
            <p>This is the actual text we want.</p>
            <footer>Footer</footer>
        </body>
    </html>
    \"\"\"
    text = tool._extract_text(html)
    assert "Main Content" in text
    assert "This is the actual text we want." in text
    
    # These should be removed
    assert "alert(1);" not in text
    assert "color: red;" not in text
    assert "Menu" not in text
    assert "Footer" not in text
    assert "Header" not in text

@pytest.mark.asyncio
async def test_mock_search_provider():
    # Use WebSearchTool which will use MockProvider by default unless configured otherwise
    # Assuming config is Mock
    tool = WebSearchTool()
    context = ToolExecutionContext(user_id=1, conversation_id=1, request_id="req", tool_call_id="tc1")
    
    res = await tool.execute(context, {"query": "test query"})
    
    assert res.success == True
    assert "results" in res.data
    assert len(res.data["results"]) > 0
    assert "Mock Result" in res.data["results"][0]["title"]
