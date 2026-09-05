from app.runtime.node import EdgeJARVISNode

if __name__ == "__main__":
    node = EdgeJARVISNode()
    print("--- JARVIS EDGE NODE ---")
    commands = [
        "เปิดไฟห้องนอน",
        "อุณหภูมิเท่าไหร่",
        "ช่วยวางแผนเที่ยวญี่ปุ่น 5 วันหน่อย"
    ]
    
    print("\n[Network: ONLINE]")
    node.network_online = True
    for c in commands:
        print(f"User: {c}")
        print(f"Edge: {node.process_voice_command(c)}")
        
    print("\n[Network: OFFLINE]")
    node.network_online = False
    for c in commands:
        print(f"User: {c}")
        print(f"Edge: {node.process_voice_command(c)}")
