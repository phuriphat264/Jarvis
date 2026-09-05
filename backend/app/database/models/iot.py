from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.database.base import Base

class IoTDevice(Base):
    __tablename__ = "iot_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # light, switch, sensor, plug, camera
    room = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    capabilities = Column(JSON, nullable=False) # e.g., {"power": True, "brightness": True}
    status = Column(String, default="ONLINE") # ONLINE, OFFLINE
    gateway = Column(String, default="mock") # mock, mqtt, home_assistant
    topic_config = Column(JSON, nullable=True) # Gateway-specific topic/id mapping
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class IoTDeviceState(Base):
    __tablename__ = "iot_device_states"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), unique=True, nullable=False)
    
    online = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    power = Column(Boolean, nullable=True)
    brightness = Column(Integer, nullable=True)
    temperature = Column(Integer, nullable=True) # or float, keeping simple
    humidity = Column(Integer, nullable=True)
    motion = Column(Boolean, nullable=True)
    raw_state = Column(JSON, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class IoTDeviceEvent(Base):
    __tablename__ = "iot_device_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    event_type = Column(String, nullable=False) # COMMAND_SENT, STATE_CHANGED, OFFLINE, CONFIRMATION_REQUIRED
    action = Column(String, nullable=True) # e.g., turn_on, set_brightness
    value = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IoTDeviceGroup(Base):
    __tablename__ = "iot_device_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IoTAutomation(Base):
    __tablename__ = "iot_automations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    
    conditions = Column(JSON, nullable=False) # e.g., {"type": "time", "value": "18:00"} or {"type": "sensor", "device_id": 1, "field": "temperature", "operator": ">", "value": 30}
    actions = Column(JSON, nullable=False) # e.g., [{"device_id": 2, "action": "turn_on"}]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
