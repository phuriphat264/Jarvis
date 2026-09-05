import httpx
from urllib.parse import urlparse
from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult
from app.core.config import settings

class HttpGetTool(BaseTool):
    name = "http_get"
    description = "Perform HTTP GET requests to fetch data from allowed public APIs or websites."
    category = "network"
    permission_level = "external"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch, e.g. 'https://api.github.com/users/octocat'"
                }
            },
            "required": ["url"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        if not settings.HTTP_TOOL_ENABLED:
            return ToolExecutionResult(
                success=False, tool_name=self.name, error={"code": "TOOL_DISABLED", "message": "HTTP Tool is disabled by configuration."}
            )
            
        url = arguments.get("url")
        if not url:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_ARGUMENT", "message": "Missing url"})
            
        # Parse and validate domain
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if not parsed_url.scheme in ["http", "https"]:
                return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_SCHEME", "message": "Only http and https are allowed."})
                
            allowed_domains = [d.strip() for d in settings.HTTP_ALLOWED_DOMAINS.split(",") if d.strip()]
            if allowed_domains and domain not in allowed_domains:
                return ToolExecutionResult(
                    success=False, 
                    tool_name=self.name, 
                    error={"code": "PERMISSION_DENIED", "message": f"Domain {domain} is not in the allowlist."}
                )
        except Exception:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_URL", "message": "Malformed URL"})
            
        # Execute GET request safely
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT, max_redirects=3) as client:
                response = await client.get(url)
                
                # Check response size limit (from headers if available)
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > settings.HTTP_MAX_RESPONSE_SIZE:
                    return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "RESPONSE_TOO_LARGE", "message": "Content-Length exceeds maximum allowed size."})
                
                text = response.text
                if len(text) > settings.HTTP_MAX_RESPONSE_SIZE:
                    return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "RESPONSE_TOO_LARGE", "message": "Response body exceeds maximum allowed size."})
                
                # Truncate if we want to be safe, but size limit handles it mostly
                # Try parsing JSON if content type is json
                data = text
                if "application/json" in response.headers.get("Content-Type", ""):
                    try:
                        data = response.json()
                    except Exception:
                        pass # Fallback to text
                        
                return ToolExecutionResult(
                    success=True, 
                    tool_name=self.name, 
                    data={"status_code": response.status_code, "body": data}
                )
                
        except httpx.TimeoutException:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "TIMEOUT", "message": "Request timed out."})
        except httpx.RequestError as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "REQUEST_FAILED", "message": str(e)})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INTERNAL_ERROR", "message": str(e)})
