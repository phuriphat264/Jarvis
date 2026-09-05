from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from app.database.base import Base


class UserPreference(Base):
    """Active preferences (explicit or approved-learned). Single source of truth for adaptation."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    key = Column(String, nullable=False)          # e.g. "response_length"
    value = Column(String, nullable=False)        # e.g. "short"
    scope = Column(String, default="GLOBAL")      # GLOBAL | PROJECT | CONVERSATION | TASK | DEVICE
    scope_id = Column(String, nullable=True)      # Optional scope entity id

    source = Column(String, nullable=False)       # USER_EXPLICIT | BEHAVIOR
    confidence = Column(Float, default=1.0)       # 0.0–1.0
    priority = Column(Integer, default=50)        # Higher = more important (USER_EXPLICIT = 100)
    status = Column(String, default="ACTIVE")     # ACTIVE | ARCHIVED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)


class PreferenceCandidate(Base):
    """System-suggested preferences not yet approved by the user."""
    __tablename__ = "preference_candidates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    scope = Column(String, default="GLOBAL")

    confidence = Column(Float, default=0.0)
    evidence_count = Column(Integer, default=0)

    status = Column(String, default="PENDING")    # PENDING | APPROVED | REJECTED | EXPIRED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BehaviorEvent(Base):
    """Lightweight, privacy-safe behavioral signals (no raw content)."""
    __tablename__ = "behavior_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    event_type = Column(String, nullable=False)   # e.g. "RESPONSE_SHORTENED"
    context = Column(String, nullable=True)       # e.g. "GENERAL" | "RESEARCH" | "PLANNING"
    entity_type = Column(String, nullable=True)   # e.g. "TASK" | "MESSAGE"
    entity_id = Column(String, nullable=True)     # ID reference only — no raw content
    metadata = Column(JSON, nullable=True)        # Structured signals only

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PersonalizationFeedback(Base):
    """Thumbs-up / thumbs-down on JARVIS responses and recommendations."""
    __tablename__ = "personalization_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    preference_id = Column(Integer, ForeignKey("user_preferences.id"), nullable=True)

    feedback_type = Column(String, nullable=False)  # USEFUL | NOT_USEFUL | TOO_LONG | TOO_SHORT | NOT_RELEVANT
    context = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
