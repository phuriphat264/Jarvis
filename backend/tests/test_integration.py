import pytest
from app.utils.encryption import SecretEncryptionService

def test_encryption_service():
    original_text = "test_token_123"
    encrypted = SecretEncryptionService.encrypt(original_text)
    assert encrypted != original_text
    
    decrypted = SecretEncryptionService.decrypt(encrypted)
    assert decrypted == original_text

def test_encryption_handles_none():
    assert SecretEncryptionService.encrypt(None) is None
    assert SecretEncryptionService.decrypt(None) is None

# Models validation
def test_integration_model():
    from app.database.models.integration import IntegrationConnection
    conn = IntegrationConnection(user_id=1, provider="google_calendar", status="CONNECTED")
    assert conn.provider == "google_calendar"
    assert conn.status == "CONNECTED"
