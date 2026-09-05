from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.world_model import ProactiveRecommendation, IntelligenceSettings, Routine
from app.world_model.context_aggregator import ContextAggregator
from app.world_model.situation_engine import SituationEngine
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("/world")
async def get_world_model(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    snapshot = await ContextAggregator.get_snapshot(current_user.id, db)
    situations = SituationEngine.detect_situations(snapshot)
    
    return {
        "success": True,
        "data": {
            "current_time": snapshot.current_time.isoformat(),
            "situations": [s.dict() for s in situations],
            "today_tasks": snapshot.today_tasks,
            "upcoming_events": snapshot.upcoming_events,
            "home_state": snapshot.home_state,
            "edge_state": snapshot.edge_state
        }
    }

@router.get("/recommendations")
async def get_recommendations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ProactiveRecommendation).where(
            ProactiveRecommendation.user_id == current_user.id,
            ProactiveRecommendation.status == "ACTIVE"
        ).order_by(ProactiveRecommendation.created_at.desc())
    )
    recs = res.scalars().all()
    
    return {
        "success": True,
        "data": [{"id": r.id, "type": r.type, "message": r.message, "priority": r.priority, "created_at": r.created_at.isoformat()} for r in recs]
    }

@router.post("/recommendations/{rec_id}/dismiss")
async def dismiss_recommendation(rec_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ProactiveRecommendation).where(ProactiveRecommendation.id == rec_id, ProactiveRecommendation.user_id == current_user.id))
    rec = res.scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    rec.status = "DISMISSED"
    await db.commit()
    return {"success": True}

@router.get("/settings")
async def get_intelligence_settings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(IntelligenceSettings).where(IntelligenceSettings.user_id == current_user.id))
    settings = res.scalars().first()
    
    if not settings:
        settings = IntelligenceSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    return {
        "success": True,
        "data": {
            "proactive_assistant_enabled": settings.proactive_assistant_enabled,
            "quiet_hours_start": settings.quiet_hours_start,
            "quiet_hours_end": settings.quiet_hours_end,
            "deadline_warnings_enabled": settings.deadline_warnings_enabled
        }
    }
