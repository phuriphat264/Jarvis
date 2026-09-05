class LocalIntentClassifier:
    def classify(self, text: str) -> dict:
        text = text.lower()
        if "เปิด" in text and "ไฟ" in text:
            return {"intent": "LIGHT_ON", "confidence": 0.95, "handled_locally": True}
        if "ปิด" in text and "ไฟ" in text:
            return {"intent": "LIGHT_OFF", "confidence": 0.95, "handled_locally": True}
        if "อุณหภูมิ" in text:
            return {"intent": "SENSOR_TEMPERATURE", "confidence": 0.90, "handled_locally": True}
        
        return {"intent": "UNKNOWN", "handled_locally": False, "reason": "CAPABILITY_NOT_AVAILABLE"}
