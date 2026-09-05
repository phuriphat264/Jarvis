from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.core.dependencies import get_current_user
from app.core_service.personal_os_context import PersonalOSContextBuilder

router = APIRouter()

@router.get("/today")
async def get_daily_briefing(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    summary = await PersonalOSContextBuilder.build_context(db, current_user.id)
    if not summary:
        summary = "No tasks or events for today."
    
    return {
        "text": summary,
        "date": "Today"
    }
