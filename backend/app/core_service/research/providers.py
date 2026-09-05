from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import httpx
from app.core.config import settings

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    domain: Optional[str] = None
    published_at: Optional[str] = None

class BaseSearchProvider:
    async def search(self, query: str, max_results: int = 5, **kwargs) -> List[SearchResult]:
        raise NotImplementedError

class MockSearchProvider(BaseSearchProvider):
    async def search(self, query: str, max_results: int = 5, **kwargs) -> List[SearchResult]:
        # Return mock results based on query or just generic ones
        return [
            SearchResult(
                title=f"Mock Result 1 for {query}",
                url="https://example.com/mock-1",
                snippet=f"This is a mock snippet containing details about {query}.",
                domain="example.com"
            ),
            SearchResult(
                title=f"Mock Result 2 for {query}",
                url="https://example.com/mock-2",
                snippet=f"More mock information regarding {query} here.",
                domain="example.com"
            )
        ][:max_results]

class BraveSearchProvider(BaseSearchProvider):
    async def search(self, query: str, max_results: int = 5, **kwargs) -> List[SearchResult]:
        if not settings.SEARCH_API_KEY:
            # Fallback or error
            return []
            
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": settings.SEARCH_API_KEY
        }
        params = {
            "q": query,
            "count": min(max_results, 20)
        }
        
        # Add freshness if specified (e.g. "pd", "pw", "pm", "py")
        freshness = kwargs.get("freshness")
        if freshness in ["pd", "pw", "pm", "py"]:
            params["freshness"] = freshness
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                web_results = data.get("web", {}).get("results", [])
                
                for item in web_results[:max_results]:
                    domain = item.get("meta_url", {}).get("netloc", "")
                    age = item.get("age", "")
                    
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        domain=domain,
                        published_at=age if age else None
                    ))
                return results
        except Exception:
            return []

class SearchProviderFactory:
    @staticmethod
    def get_provider() -> BaseSearchProvider:
        provider = settings.SEARCH_PROVIDER.lower()
        if provider == "brave":
            return BraveSearchProvider()
        return MockSearchProvider()
