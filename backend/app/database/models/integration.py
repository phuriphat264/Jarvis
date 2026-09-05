from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.database.base import Base

class IntegrationConnection(Base):
    __tablename__ = "integration_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    provider = Column(String, nullable=False, index=True)
    status = Column(String, default="CONNECTED") # CONNECTED, AUTH_REQUIRED, DISCONNECTED, ERROR
    external_account_id = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    scopes = Column(String, nullable=True)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PendingAction(Base):
    __tablename__ = "pending_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    arguments = Column(JSON, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, CONFIRMED, REJECTED, EXPIRED, EXECUTED, FAILED
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True)
    line_enabled = Column(Boolean, default=False)
    telegram_enabled = Column(Boolean, default=False)
    email_enabled = Column(Boolean, default=False)
    quiet_hours_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(String, default="23:00")
    quiet_hours_end = Column(String, default="07:00")
    daily_summary_enabled = Column(Boolean, default=True)
    meeting_reminder_enabled = Column(Boolean, default=True)
    task_overdue_enabled = Column(Boolean, default=True)
