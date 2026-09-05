from typing import Dict, Any
from app.interfaces.integration import BaseIntegration, IntegrationCapability

class MockGoogleCalendar(BaseIntegration):
    name = "Google Calendar"
    provider = "google_calendar"
    capabilities = [IntegrationCapability.READ, IntegrationCapability.WRITE, IntegrationCapability.DELETE]
    scopes = ["https://www.googleapis.com/auth/calendar"]

    async def get_auth_url(self, user_id: int, redirect_uri: str) -> str:
        return f"https://mock-oauth.com/auth?client_id=mock&redirect_uri={redirect_uri}&state={user_id}"

    async def exchange_code(self, user_id: int, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {
            "access_token": "mock_access_token_gcal",
            "refresh_token": "mock_refresh_token_gcal",
            "expires_in": 3600
        }

class MockGmail(BaseIntegration):
    name = "Gmail"
    provider = "gmail"
    capabilities = [IntegrationCapability.READ] # Read only as per prompt
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    async def get_auth_url(self, user_id: int, redirect_uri: str) -> str:
        return f"https://mock-oauth.com/auth/gmail?client_id=mock&redirect_uri={redirect_uri}&state={user_id}"

    async def exchange_code(self, user_id: int, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {
            "access_token": "mock_access_token_gmail",
            "refresh_token": "mock_refresh_token_gmail",
            "expires_in": 3600
        }

class MockLine(BaseIntegration):
    name = "LINE"
    provider = "line"
    capabilities = [IntegrationCapability.WRITE]
    scopes = ["profile", "message.write"]

    async def get_auth_url(self, user_id: int, redirect_uri: str) -> str:
        return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=mock&redirect_uri={redirect_uri}&state={user_id}"

    async def exchange_code(self, user_id: int, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {
            "access_token": "mock_access_token_line",
            "refresh_token": "mock_refresh_token_line",
            "expires_in": 2592000
        }

class MockTelegram(BaseIntegration):
    name = "Telegram"
    provider = "telegram"
    capabilities = [IntegrationCapability.WRITE]
    scopes = [] # Usually token based

    async def get_auth_url(self, user_id: int, redirect_uri: str) -> str:
        return f"https://telegram.org/mock-auth?state={user_id}"

    async def exchange_code(self, user_id: int, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {
            "access_token": "mock_access_token_telegram",
            "refresh_token": None,
            "expires_in": 0
        }

from app.interfaces.integration import integration_registry
integration_registry.register(MockGoogleCalendar())
integration_registry.register(MockGmail())
integration_registry.register(MockLine())
integration_registry.register(MockTelegram())
