import requests
import json
import time
import os
import sys

# ---------- تنظیمات ----------
# توکن رو از Environment Variable میگیریم (امن تر)
TOKEN = os.environ.get("RUBIKA_TOKEN", "HJFED0ZQCFZBHGGYLIJEDGTNWHZYADISAFIHKRZRMKCXMNSCWLPVREZNRSMLGNWW")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    data = {"timeout": 10}
    if offset:
        data["offset"] = offset
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📦 Response: {json.dumps(result, indent=2)[:200]}...")
            return result.get("data", {}).get("updates", [])
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return []
    except requests.exceptions.Timeout:
        print("❌ Timeout: سرور روبیکا پاسخ نداد")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        print(f"📤 Send status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Send error: {e}")
        return False

def main():
    offset = None
    print("🚀 ربات تست روبیکا فعال شد!")
    print(f"🔗 آدرس: {BASE_URL}")
    print("⏳ منتظر پیام... (Ctrl+C توقف)")
    print("-" * 50)

    while True:
        try:
            updates = get_updates(offset)

            for update in updates:
                if "update_id" in update:
                    offset = int(update["update_id"]) + 1
                    print(f"🆔 Update ID: {offset}")

                if update.get("type") == "NewMessage":
                    chat_id = update["chat_id"]
                    msg = update["new_message"].get("text", "[رسانه]")
                    print(f"💬 پیام از {chat_id}: {msg[:50]}")
                    
                    # پاسخ Echo
                    result = send_message(chat_id, f"👋 سلام! Echo: {msg}")
                    if result:
                        print("✅ پاسخ ارسال شد")
                    else:
                        print("❌ پاسخ ارسال نشد")

            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n🛑 ربات متوقف شد.")
            break
        except Exception as e:
            print(f"❌ Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
