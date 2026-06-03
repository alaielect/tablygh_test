import requests
import os
import time

TOKEN = os.environ.get("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

print("🚀 ربات تست ساده روبیکا")
print(f"🔗 توکن: {TOKEN[:20]}...")

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    data = {"timeout": 10}
    if offset:
        data["offset"] = offset
    
    try:
        response = requests.post(url, json=data, timeout=20)
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            updates = result.get("data", {}).get("updates", [])
            print(f"📦 دریافت {len(updates)} آپدیت")
            return updates
        else:
            print(f"❌ خطا: {response.text[:200]}")
            return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Send error: {e}")
        return False

def main():
    offset = None
    print("⏳ در انتظار پیام...")
    print("💡 لطفاً یک پیام در گروه بفرستید\n")
    
    while True:
        updates = get_updates(offset)
        
        for update in updates:
            if "update_id" in update:
                offset = update["update_id"] + 1
                print(f"🆔 Update ID: {offset}")
            
            if update.get("type") == "NewMessage":
                msg = update.get("new_message", {})
                chat_id = update.get("chat_id")
                text = msg.get("text", "[بدون متن]")
                user_guid = msg.get("sender_user_guid", "ناشناس")
                
                print(f"\n📩 پیام جدید!")
                print(f"   Chat ID: {chat_id}")
                print(f"   User GUID: {user_guid}")
                print(f"   متن: {text}")
                
                # پاسخ echo
                reply = f"سلام! پیام شما دریافت شد:\n{text}"
                send_message(chat_id, reply)
                print(f"✅ پاسخ ارسال شد\n")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
