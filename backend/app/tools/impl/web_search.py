from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult
from app.core_service.research.providers import SearchProviderFactory
from app.core.config import settings

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for up-to-date information, news, or factual answers."
    category = "research"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query."
                },
                "freshness": {
                    "type": "string",
                    "description": "Optional freshness constraint: 'pd' (past day), 'pw' (past week), 'pm' (past month), 'py' (past year).",
                    "enum": ["pd", "pw", "pm", "py"]
                }
            },
            "required": ["query"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        query = arguments.get("query")
        freshness = arguments.get("freshness")
        
        if not query:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_ARGUMENT", "message": "Missing query"})
            
        provider = SearchProviderFactory.get_provider()
        
        try:
            # We enforce a configurable max sources per query from settings
            results = await provider.search(query, max_results=settings.MAX_SOURCES_PER_QUERY, freshness=freshness)
            
            # Remove duplicate URLs if any
            seen_urls = set()
            unique_results = []
            for r in results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    unique_results.append(r.model_dump())
                    
            if not unique_results:
                return ToolExecutionResult(success=True, tool_name=self.name, data={"results": [], "message": "No results found."})
                
            return ToolExecutionResult(success=True, tool_name=self.name, data={"results": unique_results})
            
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "SEARCH_FAILED", "message": str(e)})
