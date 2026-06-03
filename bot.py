import requests
import json
import time
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import numpy as np

# ---------- تنظیمات ----------
TOKEN = os.environ.get("RUBIKA_TOKEN")
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

# ⚠️ IMPORTANT: chat_id گروه خودت رو اینجا بذار (اگه نمی‌دونی، بذار None)
# برای پیدا کردن chat_id: اول با ALLOWED_CHAT_ID = None اجرا کن، بعد تو لاگ ببین
ALLOWED_CHAT_ID = None  # <--- این رو بعد پیدا کردن عدد، عوض کن

# ---------- مدل هوش مصنوعی تشخیص تبلیغ ----------
print("🔄 Loading AI model...")

# داده‌های آموزشی ساده
ad_examples = [
    "کتاب های خودم رو میفروشم", "لینک در بیو", "برای خرید پیام بدید",
    "تخفیف ویژه", "سفارش اینستاگرام", "فروش ویژه"
]
normal_examples = [
    "سلام چطوری", "فیلم خوب دیدی", "کتاب خوب معرفی کن",
    "امروز هوا خوبه", "ممنون بابت راهنمایی"
]

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text

all_texts = [normalize_text(t) for t in ad_examples + normal_examples]
all_labels = [1]*len(ad_examples) + [0]*len(normal_examples)

vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=100)
X = vectorizer.fit_transform(all_texts)
model = LinearSVC(C=1.0, max_iter=500)
model.fit(X, all_labels)
print("✅ AI model ready!")

def is_ad_text(text):
    if not text or len(text) < 5:
        return False
    try:
        vec = vectorizer.transform([normalize_text(text)])
        return model.predict(vec)[0] == 1
    except:
        return False

# ---------- توابع تشخیص سریع ----------
def has_link(text):
    return bool(re.search(r'https?://|t\.me|@[\w]+|\.(ir|com|org)', text, re.I))

def is_forwarded(update):
    return update.get("new_message", {}).get("forwarded_from") is not None

# ---------- توابع مدیریت ----------
def delete_msg(chat_id, msg_id):
    try:
        requests.post(f"{BASE_URL}/deleteMessage", 
                     json={"chat_id": chat_id, "message_id": msg_id},
                     headers={'Content-Type': 'application/json'}, timeout=5)
    except: pass

def send_warning(chat_id, user_guid, reason):
    text = f"⚠️ پیام شما حذف شد\nعلت: {reason}"
    try:
        resp = requests.post(f"{BASE_URL}/sendMessage",
                            json={"chat_id": chat_id, "text": text, "user_guid": user_guid},
                            headers={'Content-Type': 'application/json'}, timeout=5)
        if resp.status_code == 200:
            msg_id = resp.json().get("data", {}).get("message_id")
            if msg_id:
                time.sleep(8)
                delete_msg(chat_id, msg_id)
    except: pass

# ---------- دریافت پیام ----------
def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    data = {"timeout": 5}
    if offset:
        data["offset"] = offset
    try:
        resp = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("updates", [])
    except Exception as e:
        print(f"Error: {e}")
    return []

# ---------- حلقه اصلی (با تاخیر مناسب) ----------
def main():
    offset = None
    print("🚀 Bot started!")
    
    while True:
        try:
            updates = get_updates(offset)
            
            for update in updates:
                if "update_id" in update:
                    offset = update["update_id"] + 1
                
                chat_id = update.get("chat_id")
                
                # اگر ALLOWED_CHAT_ID تنظیم شده و با این گروه فرق داره، نادیده بگیر
                if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
                    continue
                
                # اگه ALLOWED_CHAT_ID هنوز None هست، این گروه رو ثبت کن
                if ALLOWED_CHAT_ID is None and chat_id:
                    print(f"\n🎯 GROUP CHAT_ID FOUND: {chat_id}")
                    print("🔒 Copy this number and set ALLOWED_CHAT_ID in code!\n")
                    ALLOWED_CHAT_ID = chat_id  # موقتاً ذخیره کن
                
                if update.get("type") == "NewMessage":
                    msg = update.get("new_message", {})
                    msg_id = msg.get("message_id")
                    user_guid = msg.get("sender_user_guid")
                    text = msg.get("text", "")
                    
                    if not text:
                        continue
                    
                    # بررسی تخلف
                    is_violation = False
                    reason = ""
                    
                    if has_link(text):
                        is_violation = True
                        reason = "لینک"
                    elif is_forwarded(update):
                        is_violation = True
                        reason = "فوروارد"
                    elif is_ad_text(text):
                        is_violation = True
                        reason = "تبلیغ"
                    
                    if is_violation:
                        print(f"🗑️ Deleted: {text[:40]}... ({reason})")
                        delete_msg(chat_id, msg_id)
                        send_warning(chat_id, user_guid, reason)
                    else:
                        print(f"✅ OK: {text[:40]}...")
            
            time.sleep(2)  # تاخیر 2 ثانیه برای جلوگیری از اسپم
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
