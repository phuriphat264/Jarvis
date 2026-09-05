import base64
import os
from cryptography.fernet import Fernet
from app.core.config import settings

class SecretEncryptionService:
    @staticmethod
    def _get_cipher():
        # Ensure key is valid 32 url-safe base64
        key = settings.ENCRYPTION_KEY
        if not key:
            # Fallback for dev if missing, but should be set in prod
            key = base64.urlsafe_b64encode(b"0"*32).decode()
        return Fernet(key.encode('utf-8'))

    @staticmethod
    def encrypt(data: str) -> str:
        if not data:
            return data
        cipher = SecretEncryptionService._get_cipher()
        return cipher.encrypt(data.encode('utf-8')).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        cipher = SecretEncryptionService._get_cipher()
        return cipher.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
