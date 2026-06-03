import requests
import os
import time

TOKEN = os.environ.get("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def get_updates():
    url = f"{BASE_URL}/getUpdates"
    data = {"timeout": 10}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, json=data, headers=headers, timeout=30)
    if response.status_code == 200:
        result = response.json()
        updates = result.get("data", {}).get("updates", [])
        for update in updates:
            if update.get("type") == "NewMessage":
                chat_id = update.get("chat_id")
                print(f"✅ chat_id گروه شما: {chat_id}")
                return chat_id
    return None

if __name__ == "__main__":
    print("🔍 در حال انتظار برای دریافت پیام از گروه...")
    print("📱 لطفاً یک پیام در گروه بفرستید")
    
    while True:
        chat_id = get_updates()
        if chat_id:
            print(f"🎯 chat_id پیدا شد: {chat_id}")
            break
        time.sleep(2)
