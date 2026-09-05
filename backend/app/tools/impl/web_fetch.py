import httpx
import ipaddress
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult
from app.core.config import settings

class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "Fetch and extract text content from a public webpage."
    category = "research"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch."
                }
            },
            "required": ["url"]
        }
        
    def _is_safe_url(self, url: str) -> bool:
        """SSRF Protection: Check if URL points to localhost or private IPs."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False
                
            hostname = parsed.hostname
            if not hostname:
                return False
                
            # Resolve IP
            ip_addr = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_addr)
            
            # Block private, loopback, multicast, etc.
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
                
            # Block cloud metadata endpoints explicitly (AWS, GCP, Azure usually use link-local 169.254.169.254, but let's be sure)
            if str(ip) == "169.254.169.254":
                return False
                
            return True
        except Exception:
            return False

    def _extract_text(self, html_content: str) -> str:
        """Extract clean text from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove useless tags
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
            element.decompose()
            
        # Get text
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up multiple newlines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        url = arguments.get("url")
        if not url:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_ARGUMENT", "message": "Missing url"})
            
        if not self._is_safe_url(url):
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "SECURITY_ERROR", "message": "Unsafe or unsupported URL."})
            
        try:
            async with httpx.AsyncClient(timeout=10.0, max_redirects=3, follow_redirects=True) as client:
                # Use a standard user agent to avoid basic blocks
                headers = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0; +http://jarvis.local)"}
                response = await client.get(url, headers=headers)
                
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "UNSUPPORTED_CONTENT", "message": f"Unsupported content type: {content_type}"})
                
                # Check response size limit (from headers if available)
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > settings.HTTP_MAX_RESPONSE_SIZE:
                    return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "RESPONSE_TOO_LARGE", "message": "Content-Length exceeds maximum allowed size."})
                
                html_content = response.text
                if len(html_content) > settings.HTTP_MAX_RESPONSE_SIZE:
                    html_content = html_content[:settings.HTTP_MAX_RESPONSE_SIZE] # Truncate if too large
                    
                text_content = self._extract_text(html_content)
                
                # Truncate to MAX_CONTENT_LENGTH_PER_SOURCE
                if len(text_content) > settings.MAX_CONTENT_LENGTH_PER_SOURCE:
                    text_content = text_content[:settings.MAX_CONTENT_LENGTH_PER_SOURCE] + "... [TRUNCATED]"
                    
                return ToolExecutionResult(
                    success=True, 
                    tool_name=self.name, 
                    data={"url": url, "content": text_content}
                )
                
        except httpx.TimeoutException:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "TIMEOUT", "message": "Request timed out."})
        except httpx.RequestError as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "REQUEST_FAILED", "message": str(e)})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INTERNAL_ERROR", "message": str(e)})
