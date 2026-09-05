# JARVIS IoT & Smart Home Architecture (Phase 14)

## Overview
Phase 14 connects JARVIS to the physical world while maintaining absolute safety. Instead of granting the LLM direct network/MQTT access, the system uses an `IoTGateway` abstraction managed strictly by the backend.

## 1. Safety & Abstraction Layers
The LLM can **never** construct raw MQTT topics, build arbitrary JSON payloads, or execute shell commands to interact with devices.

**Flow:**
`User Request` -> `IoTAgent` (Phase 13 Specialist) -> `ToolExecutor` (iot_device_control) -> `IoTSafetyPolicy` -> `DeviceRegistry` -> `IoTGateway` (Mock/MQTT) -> `Physical Device`

## 2. IoTSafetyPolicy
Every physical action must pass the `IoTSafetyPolicy`.
- **SAFE_READ**: (Sensors, Status) No confirmation required.
- **LOW_RISK**: (Lights) Usually no confirmation required if authorized.
- **MEDIUM_RISK**: (Smart Plugs) May require confirmation.
- **HIGH_RISK**: (Locks, Heaters, Ovens) **Always** require strict explicit user confirmation. High-risk devices cannot be controlled autonomously via automations.

## 3. Device Capabilities
JARVIS respects device limits. If a device has `{"power": true, "brightness": false}`, any attempt to set brightness is rejected by the backend before reaching the gateway.

## 4. Gateways
- **MockIoTGateway**: Enabled by default (`IOT_MOCK_MODE=True`). Simulates state changes in-memory so developers can test UI and AI logic without physical hardware.
- **MQTTGateway**: Configured via `.env` credentials. Manages TLS and prevents credential exposure.

## 5. UI Integration
- `/devices`: Frontend control center for manually toggling devices and viewing sensor data.
- Dashboard: Provides a high-level summary of active automations and online devices.
