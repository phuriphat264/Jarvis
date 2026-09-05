from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from app.database.base import Base

class EdgeNode(Base):
    __tablename__ = "edge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    node_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="PENDING_ENROLLMENT") # PENDING_ENROLLMENT, ONLINE, OFFLINE, DEGRADED, REVOKED
    
    hardware_info = Column(JSON, nullable=True) # CPU, RAM, Temp
    software_version = Column(String, nullable=True)
    capabilities = Column(JSON, nullable=True) # STT, TTS, Vision
    
    auth_key = Column(String, nullable=True) # Hashed/encrypted credential for node
    
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EdgeEnrollment(Base):
    __tablename__ = "edge_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    enrollment_code = Column(String, unique=True, index=True, nullable=False)
    
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EdgeEvent(Base):
    __tablename__ = "edge_events"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("edge_nodes.node_id"), index=True, nullable=False)
    event_type = Column(String, nullable=False) # e.g. EDGE_COMMAND_LOCAL, EDGE_CONFIG_SYNCED
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
