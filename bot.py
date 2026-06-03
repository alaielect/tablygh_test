import requests
import os
import time

TOKEN = os.environ.get("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

print("="*50)
print("🚀 ربات تست روبیکا")
print("="*50)

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"📤 Send status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Send error: {e}")
        return False

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    data = {"timeout": 10, "offset": offset} if offset else {"timeout": 10}
    
    try:
        response = requests.post(url, json=data, timeout=20)
        if response.status_code == 200:
            result = response.json()
            updates = result.get("data", {}).get("updates", [])
            return updates, result
        else:
            print(f"❌ Status {response.status_code}")
            return [], None
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], None

def main():
    offset = None
    print("⏳ در حال دریافت پیام‌ها...")
    print("💡 لطفاً در گروه یک پیام بفرستید\n")
    
    while True:
        updates, raw = get_updates(offset)
        
        if updates:
            print(f"\n📦 {len(updates)} آپدیت جدید!")
            
            for update in updates:
                update_id = update.get("update_id")
                if update_id:
                    offset = update_id + 1
                
                chat_id = update.get("chat_id")
                update_type = update.get("type")
                
                print(f"   🆔 Update ID: {update_id}")
                print(f"   💬 Chat ID: {chat_id}")
                print(f"   📌 Type: {update_type}")
                
                if update_type == "NewMessage":
                    msg = update.get("new_message", {})
                    text = msg.get("text", "[بدون متن]")
                    user_guid = msg.get("sender_user_guid", "ناشناس")
                    
                    print(f"   👤 User: {user_guid}")
                    print(f"   📝 Text: {text}")
                    
                    # ارسال پاسخ تست
                    send_message(chat_id, f"✅ پیام شما دریافت شد!\nمتن: {text[:50]}")
                    
                    # چاپ chat_id مهم
                    print(f"\n🎯 CHAT_ID این گروه: {chat_id}")
                    print("🔒 این عدد رو برای تنظیم ALLOWED_CHAT_ID ذخیره کن!\n")
        
        time.sleep(3)

if __name__ == "__main__":
    main()
