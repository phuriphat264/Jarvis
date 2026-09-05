from app.command_router.classifier import LocalIntentClassifier

class EdgeJARVISNode:
    def __init__(self):
        self.classifier = LocalIntentClassifier()
        self.network_online = True
        self.node_id = "test_node"
        
    def process_voice_command(self, text: str) -> str:
        # 1. Local offline classification
        result = self.classifier.classify(text)
        
        # 2. Local Handle
        if result["handled_locally"]:
            # Normally this would trigger Local Device Control -> MQTT
            return f"Executed {result['intent']} locally with {result['confidence']*100}% confidence."
            
        # 3. Server Fallback
        if self.network_online:
            return f"Forwarding '{text}' to Server..."
        else:
            return "ตอนนี้ผมทำงานแบบ Offline อยู่ครับ งานนี้ต้องเชื่อมต่อ Server ก่อน"
