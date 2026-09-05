from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger("jarvis.iot_safety")

class IoTSafetyPolicy:
    HIGH_RISK_TYPES = ["lock", "garage", "security", "heater", "oven", "valve"]
    MEDIUM_RISK_TYPES = ["plug", "switch", "camera"]
    LOW_RISK_TYPES = ["light", "fan"]
    SAFE_READ_TYPES = ["sensor"]

    @classmethod
    def determine_risk_and_confirmation(cls, device_type: str, action: str) -> Tuple[str, bool]:
        """Returns (RiskLevel, RequiresConfirmation)"""
        if action == "status" or action == "read":
            return ("SAFE_READ", False)
            
        if device_type in cls.HIGH_RISK_TYPES:
            return ("HIGH_RISK", True)
            
        if device_type in cls.MEDIUM_RISK_TYPES:
            # Medium risk might be configurable, defaulting to True for safety
            return ("MEDIUM_RISK", True)
            
        if device_type in cls.LOW_RISK_TYPES:
            return ("LOW_RISK", False)
            
        # Default fallback
        return ("UNKNOWN", True)
        
    @classmethod
    def validate_action(cls, capabilities: Dict[str, Any], action: str, kwargs: Dict[str, Any]) -> bool:
        if action == "turn_on" or action == "turn_off":
            return capabilities.get("power", False)
            
        if action == "set_brightness":
            return capabilities.get("brightness", False) and "value" in kwargs
            
        return False
