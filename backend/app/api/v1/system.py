from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "jarvis-backend"
    }

@router.get("/status")
def system_status():
    return {
        "backend": "ok",
        "database": "connected (mock)",
        "ai_provider": settings.AI_PROVIDER,
        "memory": "ok (mock)",
        "tools": "ready (mock)"
    }
