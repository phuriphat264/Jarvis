# JARVIS Phase 15: Edge Processing & Hardware Deployment

## Architectural Vision
JARVIS operates as a Hybrid Cloud + Edge system. The Main AI Server handles complex reasoning, memory, web research, and agent tasks. Edge Nodes (typically Raspberry Pis) handle localized, real-time tasks and act as a reliable fallback when the internet disconnects.

### Why Edge?
1. **Low Latency**: Simple tasks (turning on a light) skip the cloud trip entirely.
2. **Offline Support**: Even if internet fails, standard home automations and local voice intents continue to operate.
3. **Privacy**: Voice audio (STT) can be processed locally without streaming continuous audio to the server.

## Components

### Server Side
- **Edge Enrollment**: Issues one-time 6-digit codes and generates 256-bit secure `auth_key`s for authenticated nodes. Nodes without valid keys are rejected from syncing.
- **Node Management**: Tracks Node CPU, RAM, Temp, and allows users to remotely revoke a compromised node.

### Edge Side (`/edge/app`)
- **Local Intent Classifier**: A lightweight NLP router. E.g., translates "เปิดไฟ" into `LIGHT_ON` locally.
- **Offline Node Runtime**: When `network_online = False`, the Edge node relies entirely on the local classifier to parse commands. If a command requires server capability (e.g., "Research Japanese vacation"), it politely declines and requests a network connection.

## Security Model
- **No Direct Master Secrets**: The Raspberry Pi Edge node does NOT contain the main OpenAI or Database credentials. It receives a scoped `auth_key`.
- **Replay Protection**: Edge API/MQTT communication utilizes nonces and timestamps.
- **Least Privilege**: Even if a node is compromised, it cannot execute tasks outside its approved capabilities (e.g., it cannot control HIGH_RISK IoT locks unless pre-authorized).
