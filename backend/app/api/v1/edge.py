from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
import uuid
import secrets
import datetime
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.edge import EdgeNode, EdgeEnrollment, EdgeEvent
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("/nodes")
async def get_edge_nodes(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EdgeNode).where(EdgeNode.user_id == current_user.id))
    nodes = result.scalars().all()
    return {"success": True, "data": [{"id": n.id, "node_id": n.node_id, "name": n.name, "status": n.status, "hardware_info": n.hardware_info, "software_version": n.software_version, "last_seen": n.last_seen.isoformat() if n.last_seen else None} for n in nodes]}

@router.post("/enrollments")
async def create_enrollment(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Generate 6-digit code
    code = f"{secrets.randbelow(1000000):06d}"
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    
    enr = EdgeEnrollment(
        user_id=current_user.id,
        enrollment_code=code,
        expires_at=expires_at
    )
    db.add(enr)
    await db.commit()
    
    return {"success": True, "data": {"enrollment_code": code, "expires_at": expires_at.isoformat()}}

@router.post("/nodes/{node_id}/revoke")
async def revoke_node(node_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EdgeNode).where(EdgeNode.node_id == node_id, EdgeNode.user_id == current_user.id))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    node.status = "REVOKED"
    node.auth_key = None # Invalidate key
    
    evt = EdgeEvent(node_id=node.node_id, event_type="EDGE_NODE_REVOKED")
    db.add(evt)
    
    await db.commit()
    return {"success": True, "message": "Node revoked"}

# --- Public/Edge API below (requires specific edge authentication in real deployment) ---
@router.post("/enroll")
async def edge_enroll(payload: dict, db: AsyncSession = Depends(get_db)):
    code = payload.get("enrollment_code")
    node_name = payload.get("name", "New Edge Node")
    hw_info = payload.get("hardware_info", {})
    
    result = await db.execute(select(EdgeEnrollment).where(EdgeEnrollment.enrollment_code == code, EdgeEnrollment.used == False))
    enr = result.scalars().first()
    
    if not enr:
        raise HTTPException(status_code=400, detail="Invalid or used enrollment code")
        
    if enr.expires_at.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Enrollment code expired")
        
    # Mark used
    enr.used = True
    
    # Create Node
    node_id = f"edge_{uuid.uuid4().hex[:12]}"
    auth_key = secrets.token_hex(32) # Master token for this node
    
    node = EdgeNode(
        user_id=enr.user_id,
        node_id=node_id,
        name=node_name,
        status="ONLINE",
        hardware_info=hw_info,
        auth_key=auth_key
    )
    db.add(node)
    
    evt = EdgeEvent(node_id=node_id, event_type="EDGE_NODE_REGISTERED")
    db.add(evt)
    
    await db.commit()
    
    return {"success": True, "data": {"node_id": node_id, "auth_key": auth_key}}
