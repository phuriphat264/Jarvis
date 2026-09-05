import pytest
from app.core_service.iot_safety import IoTSafetyPolicy
from app.integrations.iot_gateway import MockIoTGateway, iot_gateway_manager

def test_iot_safety_policy():
    # Safe read
    risk, confirm = IoTSafetyPolicy.determine_risk_and_confirmation("sensor", "status")
    assert risk == "SAFE_READ"
    assert confirm is False
    
    # Low risk
    risk, confirm = IoTSafetyPolicy.determine_risk_and_confirmation("light", "turn_on")
    assert risk == "LOW_RISK"
    assert confirm is False
    
    # Medium risk
    risk, confirm = IoTSafetyPolicy.determine_risk_and_confirmation("plug", "turn_on")
    assert risk == "MEDIUM_RISK"
    assert confirm is True
    
    # High risk
    risk, confirm = IoTSafetyPolicy.determine_risk_and_confirmation("lock", "turn_on")
    assert risk == "HIGH_RISK"
    assert confirm is True

def test_capability_validation():
    caps = {"power": True, "brightness": True}
    assert IoTSafetyPolicy.validate_action(caps, "turn_on", {}) is True
    assert IoTSafetyPolicy.validate_action(caps, "set_brightness", {"value": 50}) is True
    assert IoTSafetyPolicy.validate_action(caps, "set_brightness", {}) is False # missing value
    
    bad_caps = {"power": True}
    assert IoTSafetyPolicy.validate_action(bad_caps, "set_brightness", {"value": 50}) is False

@pytest.mark.asyncio
async def test_mock_gateway():
    gw = iot_gateway_manager.get("mock")
    assert gw is not None
    await gw.connect()
    
    await gw.publish("jarvis/device/1/set", {"state": "ON"})
    state = await gw.get_state("jarvis/device/1/state")
    assert state.get("state") == "ON"
