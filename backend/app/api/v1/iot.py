from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.iot import IoTDevice, IoTDeviceState
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("/devices")
async def get_devices(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IoTDevice).where(IoTDevice.user_id == current_user.id))
    devices = result.scalars().all()
    
    # Normally we'd join states, but doing simply
    out = []
    for d in devices:
        s_result = await db.execute(select(IoTDeviceState).where(IoTDeviceState.device_id == d.id))
        state = s_result.scalars().first()
        out.append({
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "room": d.room,
            "status": d.status,
            "capabilities": d.capabilities,
            "state": {
                "online": state.online if state else False,
                "power": state.power if state else None,
                "brightness": state.brightness if state else None,
                "temperature": state.temperature if state else None
            }
        })
    return {"success": True, "data": out}

@router.post("/devices")
async def add_device(device_data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    dev = IoTDevice(
        user_id=current_user.id,
        name=device_data["name"],
        type=device_data["type"],
        room=device_data.get("room"),
        capabilities=device_data.get("capabilities", {}),
        gateway="mock"
    )
    db.add(dev)
    await db.commit()
    await db.refresh(dev)
    
    state = IoTDeviceState(device_id=dev.id, online=True)
    db.add(state)
    await db.commit()
    
    return {"success": True, "data": {"id": dev.id}}
