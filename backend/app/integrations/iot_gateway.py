import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger("jarvis.iot_gateway")

class BaseIoTGateway:
    async def connect(self):
        raise NotImplementedError
        
    async def disconnect(self):
        raise NotImplementedError
        
    async def publish(self, topic: str, payload: Dict[str, Any]):
        raise NotImplementedError

    async def get_state(self, topic: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

class MockIoTGateway(BaseIoTGateway):
    def __init__(self):
        self.connected = False
        self._states = {}

    async def connect(self):
        self.connected = True
        logger.info("MockIoTGateway connected")

    async def disconnect(self):
        self.connected = False
        logger.info("MockIoTGateway disconnected")

    async def publish(self, topic: str, payload: Dict[str, Any]):
        if not self.connected:
            raise Exception("Gateway not connected")
        logger.info(f"MockIoTGateway publishing to {topic}: {payload}")
        # Simulate state update
        state_topic = topic.replace("/set", "/state")
        if state_topic not in self._states:
            self._states[state_topic] = {}
        self._states[state_topic].update(payload)
        
    async def get_state(self, topic: str) -> Optional[Dict[str, Any]]:
        return self._states.get(topic, {})

class MQTTGateway(BaseIoTGateway):
    # In a real implementation this would use aiomqtt or paho-mqtt
    def __init__(self, config):
        self.config = config
        self.connected = False
        
    async def connect(self):
        if not self.config.MQTT_ENABLED:
            return
        # paho-mqtt setup here
        self.connected = True
        logger.info(f"MQTT connected to {self.config.MQTT_BROKER_HOST}")

    async def disconnect(self):
        self.connected = False

    async def publish(self, topic: str, payload: Dict[str, Any]):
        if not self.connected:
            raise Exception("MQTT not connected")
        logger.info(f"MQTT publish {topic}")

    async def get_state(self, topic: str) -> Optional[Dict[str, Any]]:
        return {} # Would read from cached state

class IoTGatewayManager:
    def __init__(self):
        self._gateways = {}
        
    def register(self, name: str, gateway: BaseIoTGateway):
        self._gateways[name] = gateway
        
    def get(self, name: str) -> BaseIoTGateway:
        return self._gateways.get(name)

iot_gateway_manager = IoTGatewayManager()
iot_gateway_manager.register("mock", MockIoTGateway())
