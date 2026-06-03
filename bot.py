import os
from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)
TOKEN = os.environ.get("RUBIKA_TOKEN")

# فقط برای جلوگیری از خطا در صورتی که توکن وجود نداشته باشد
if not TOKEN:
    print("❌ RUBIKA_TOKEN environment variable not set!")
    exit(1)

BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

# ------- تابع ارسال پیام (برای پاسخ دادن) -------
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code != 200:
            print(f"Failed to send message: {response.status_code}")
    except Exception as e:
        print(f"Send error: {e}")

# ------- تابع بررسی مداوم پیام‌ها (Polling) که در پس‌زمینه اجرا می‌شود -------
def polling_worker():
    offset = None
    print("🔄 Polling worker started...")
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            data = {"timeout": 10}
            if offset:
                data["offset"] = offset

            response = requests.post(url, json=data, timeout=20)
            if response.status_code == 200:
                result = response.json()
                updates = result.get("data", {}).get("updates", [])

                for update in updates:
                    if "update_id" in update:
                        offset = update["update_id"] + 1

                    # پاسخ به پیام‌های جدید
                    if update.get("type") == "NewMessage":
                        chat_id = update.get("chat_id")
                        msg = update.get("new_message", {})
                        text = msg.get("text", "")
                        user_guid = msg.get("sender_user_guid")
                        print(f"New message from {user_guid}: {text}")

                        # ارسال پاسخ
                        send_message(chat_id, f"Hello! Your message received.")
        except Exception as e:
            print(f"Polling error: {e}")
        time.sleep(2)

# ------- مسیر Webhook برای دریافت مستقیم پیام از روبیکا (اختیاری ولی بهتر) -------
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json
    print(f"Webhook received: {update}")
    
    if update.get("type") == "NewMessage":
        chat_id = update.get("chat_id")
        msg = update.get("new_message", {})
        text = msg.get("text", "")
        
        # اینجا می‌تونید پیام رو پردازش کنید
        send_message(chat_id, f"Webhook: Your message received: {text}")
    
    return jsonify({"status": "ok"}), 200

# ------- مسیر Health Check برای Render -------
@app.route("/", methods=["GET"])
def home():
    return "🤖 Rubika Bot is running!", 200

# ------- اجرا -------
if __name__ == "__main__":
    # اجرای Polling در یک ترد جداگانه
    polling_thread = threading.Thread(target=polling_worker, daemon=True)
    polling_thread.start()
    
    # اجرای وب سرور (که پورت رو باز می‌کنه)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
