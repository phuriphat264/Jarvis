from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class IntegrationCapability:
    READ = "READ_EXTERNAL"
    WRITE = "WRITE_EXTERNAL"
    DELETE = "DELETE_EXTERNAL"

class BaseIntegration:
    name: str
    provider: str
    capabilities: List[str]
    scopes: List[str]

    async def get_auth_url(self, user_id: int, redirect_uri: str) -> str:
        raise NotImplementedError

    async def exchange_code(self, user_id: int, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchanges code for tokens (access, refresh, expires_at)"""
        raise NotImplementedError

class IntegrationRegistry:
    def __init__(self):
        self._integrations: Dict[str, BaseIntegration] = {}

    def register(self, integration: BaseIntegration):
        self._integrations[integration.provider] = integration

    def get(self, provider: str) -> Optional[BaseIntegration]:
        return self._integrations.get(provider)

    def list_all(self) -> List[BaseIntegration]:
        return list(self._integrations.values())

integration_registry = IntegrationRegistry()
