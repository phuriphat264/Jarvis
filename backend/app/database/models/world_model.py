from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.sql import func
from app.database.base import Base

class IntelligenceSettings(Base):
    __tablename__ = "intelligence_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, unique=True)
    
    proactive_assistant_enabled = Column(Boolean, default=True)
    proactive_voice_enabled = Column(Boolean, default=False)
    routine_suggestions_enabled = Column(Boolean, default=True)
    smart_daily_briefing_enabled = Column(Boolean, default=True)
    deadline_warnings_enabled = Column(Boolean, default=True)
    iot_suggestions_enabled = Column(Boolean, default=True)
    environment_suggestions_enabled = Column(Boolean, default=True)
    auto_low_risk_actions = Column(Boolean, default=False)
    
    quiet_hours_start = Column(String, default="22:00")
    quiet_hours_end = Column(String, default="07:00")
    max_notifications_per_day = Column(Integer, default=10)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    trigger_type = Column(String, nullable=False) # e.g. TIME, EVENT, SENSOR
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    
    status = Column(String, default="SYSTEM_SUGGESTED") # SYSTEM_SUGGESTED, ACTIVE, PAUSED, ARCHIVED
    confidence = Column(Float, nullable=True)
    source = Column(String, default="USER_CREATED") # USER_CREATED, SYSTEM_SUGGESTED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ProactiveRecommendation(Base):
    __tablename__ = "proactive_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    type = Column(String, nullable=False) # e.g. DEADLINE_WARNING, MEETING_SOON, IOT_SUGGESTION
    message = Column(String, nullable=False)
    reason = Column(JSON, nullable=True)
    
    priority = Column(String, default="NORMAL") # LOW, NORMAL, HIGH, URGENT
    action_level = Column(String, default="LEVEL_2") # LEVEL_1 (Suggest), LEVEL_2 (Notify), LEVEL_3 (Confirm)
    
    fingerprint = Column(String, nullable=False) # For deduplication
    status = Column(String, default="ACTIVE") # ACTIVE, DISMISSED, SNOOZED, ACCEPTED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("proactive_recommendations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    feedback_type = Column(String, nullable=False) # USEFUL, NOT_USEFUL, DISMISSED, SNOOZED, NEVER_AGAIN
    created_at = Column(DateTime(timezone=True), server_default=func.now())
