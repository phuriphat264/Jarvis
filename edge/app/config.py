import os

SERVER_URL = os.getenv("JARVIS_SERVER_URL", "http://localhost:8000")
NODE_ID = os.getenv("EDGE_NODE_ID", "")
AUTH_KEY = os.getenv("EDGE_AUTH_KEY", "")

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
