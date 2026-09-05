from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.integration import IntegrationConnection
from app.schemas.integration import IntegrationConnectionResponse
from app.core.dependencies import get_current_user
from app.interfaces.integration import integration_registry
from app.utils.encryption import SecretEncryptionService

router = APIRouter()

@router.get("", response_model=List[IntegrationConnectionResponse])
async def list_connections(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.user_id == current_user.id))
    return result.scalars().all()

@router.post("/{provider}/connect")
async def connect_integration(provider: str, current_user: User = Depends(get_current_user)):
    integration = integration_registry.get(provider)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration provider not found")
        
    url = await integration.get_auth_url(current_user.id, "http://localhost:3000/settings/integrations/callback")
    return {"url": url}

@router.get("/{provider}/callback")
async def callback_integration(provider: str, code: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    integration = integration_registry.get(provider)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration provider not found")
        
    try:
        tokens = await integration.exchange_code(current_user.id, code, "http://localhost:3000/settings/integrations/callback")
        
        # Check existing connection
        result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.user_id == current_user.id, IntegrationConnection.provider == provider))
        conn = result.scalars().first()
        
        enc_acc = SecretEncryptionService.encrypt(tokens.get("access_token"))
        enc_ref = SecretEncryptionService.encrypt(tokens.get("refresh_token"))
        
        if conn:
            conn.encrypted_access_token = enc_acc
            conn.encrypted_refresh_token = enc_ref
            conn.status = "CONNECTED"
            conn.display_name = f"{provider} Connected"
        else:
            conn = IntegrationConnection(
                user_id=current_user.id,
                provider=provider,
                status="CONNECTED",
                display_name=f"{provider} Connected",
                encrypted_access_token=enc_acc,
                encrypted_refresh_token=enc_ref
            )
            db.add(conn)
            
        await db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{provider}/disconnect")
async def disconnect_integration(provider: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.user_id == current_user.id, IntegrationConnection.provider == provider))
    conn = result.scalars().first()
    if conn:
        await db.delete(conn)
        await db.commit()
    return {"success": True}
