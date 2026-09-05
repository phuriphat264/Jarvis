from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult
from app.core_service.rag.retriever import RAGRetriever
from app.database.session import AsyncSessionLocal

class FileSearchTool(BaseTool):
    name = "file_search"
    description = "Search across the user's private uploaded documents/files for answers."
    category = "rag"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The semantic search query."
                },
                "document_id": {
                    "type": "string",
                    "description": "Optional specific document ID to search within."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Optional number of results to retrieve."
                }
            },
            "required": ["query"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        query = arguments.get("query")
        document_id = arguments.get("document_id")
        top_k = arguments.get("top_k")
        
        if not query:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_ARGUMENT", "message": "Missing query"})
            
        try:
            # Create a short-lived session since we're in tool execution
            async with AsyncSessionLocal() as db:
                retriever = RAGRetriever(db)
                results = await retriever.search(
                    user_id=context.user_id,
                    query=query,
                    document_id=document_id,
                    top_k=top_k
                )
                
            return ToolExecutionResult(success=True, tool_name=self.name, data={"results": results})
            
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "SEARCH_FAILED", "message": str(e)})
