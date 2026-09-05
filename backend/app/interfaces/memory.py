from typing import Any, List, Dict

class BaseMemoryService:
    async def store_memory(self, user_id: int, content: str, metadata: Dict[str, Any] = None):
        raise NotImplementedError
        
    async def search_memory(self, user_id: int, query: str) -> List[Any]:
        raise NotImplementedError
        
class MockMemoryService(BaseMemoryService):
    async def store_memory(self, user_id: int, content: str, metadata: Dict[str, Any] = None):
        pass
        
    async def search_memory(self, user_id: int, query: str) -> List[Any]:
        return []
