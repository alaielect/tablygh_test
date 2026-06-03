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

# 🔒 فقط همین گروه (chat_id گروه خودت)
ALLOWED_CHAT_ID = "b0HisEV0VWz0afc8955d2fbc55e5a5a3"

# ---------- مدل هوش مصنوعی تشخیص تبلیغ (از صفر) ----------
print("🔄 آموزش مدل هوش مصنوعی...")

# داده‌های آموزشی (تبلیغات)
ad_examples = [
    "کتاب های خودم رو میفروشم", "لینک در بیو من", "برای خرید پیام بدید",
    "بنده محصولات خودم رو میفروشم", "این پکیج رو از دست نده", "بهترین قیمت رو من دارم",
    "تخفیف ویژه", "سفارش اینستاگرام", "فروش ویژه", "کالای من عالیه",
    "خرید محصول", "ارسال به سراسر کشور", "فقط برای شما", "پیشنهاد ویژه",
    "حراجی عالی", "تولید محتوا", "کانال من", "آیدی من", "تلگرام من",
    "کتتاب های خودم رو میفروشم",  # غلط املایی
    "لینک در بییوو",  # غلط املایی
]

# داده‌های آموزشی (جملات عادی)
normal_examples = [
    "سلام بچه ها چطورین", "این فیلم رو دیدین", "کتاب خوبی برای معرفی دارید",
    "من این گوشی رو دارم عالیه", "امروز هوا خیلی خوبه", "کسی فیلم جدید دیده",
    "ممنون بابت راهنمایی", "به نظرتون این مدل خوبه", "چه خبر", "دستتون درد نکنه",
    "الان ساعت چنده", "کجا بودی", "خسته نباشید", "عکس قشنگه", "چه طور میتونم کمک کنم"
]

# نرمال کردن متن (غلط املایی رو هم میگیره)
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return text

# ساخت مدل
all_texts = [normalize_text(t) for t in ad_examples + normal_examples]
all_labels = [1]*len(ad_examples) + [0]*len(normal_examples)

vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=150, analyzer='char_wb')
X = vectorizer.fit_transform(all_texts)
y = np.array(all_labels)

model = LinearSVC(C=1.0, max_iter=1000, class_weight='balanced')
model.fit(X, y)
print("✅ مدل هوش مصنوعی آماده شد!")

def is_ad_content(text):
    """تشخیص محتوای تبلیغاتی با AI"""
    if not text or len(text) < 5:
        return False
    try:
        norm_text = normalize_text(text)
        vec = vectorizer.transform([norm_text])
        pred = model.predict(vec)[0]
        return pred == 1
    except:
        return False

# ---------- توابع تشخیص قوانین ----------
def has_link(text):
    """تشخیص لینک"""
    patterns = [
        r'https?://[^\s]+', r't\.me/[^\s]+', r'rubika\.ir/[^\s]+',
        r'@[a-zA-Z0-9_]+', r'[a-zA-Z0-9_]+\.(ir|com|org|net|io|info|xyz)'
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def has_contact_info(text):
    """تشخیص آیدی یا اطلاعات تماس"""
    patterns = [
        r'@[a-zA-Z0-9_]+', r'id:\s*[a-zA-Z0-9_]+',
        r'آیدی[:\s]*[@]?[a-zA-Z0-9_]+', r'ایدی[:\s]*[@]?[a-zA-Z0-9_]+'
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def has_forwarded_flag(update):
    """تشخیص فوروارد شده"""
    msg = update.get("new_message", {})
    return msg.get("forwarded_from") is not None

# ---------- توابع مدیریت گروه ----------
def delete_message(chat_id, message_id):
    """حذف پیام"""
    url = f"{BASE_URL}/deleteMessage"
    data = {"chat_id": chat_id, "message_id": message_id}
    try:
        requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=5)
    except Exception as e:
        print(f"Delete error: {e}")

def kick_user(chat_id, user_guid):
    """اخراج کاربر"""
    url = f"{BASE_URL}/kickUser"
    data = {"chat_id": chat_id, "user_guid": user_guid}
    try:
        requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=5)
        print(f"👢 کاربر {user_guid} اخراج شد")
    except Exception as e:
        print(f"Kick error: {e}")

def send_warning(chat_id, user_guid, reason, warning_msg_id=None):
    """ارسال پیام هشدار"""
    url = f"{BASE_URL}/sendMessage"
    text = (
        f"⚠️ *پیام شما توسط هوش مصنوعی AI شناسایی و حذف گردید.*\n"
        f"🔍 *علت:* {reason}\n\n"
        f"🛡️ تخلف بعدی = اخراج قطعی از گروه"
    )
    data = {"chat_id": chat_id, "text": text, "user_guid": user_guid}
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=5)
        if response.status_code == 200:
            result = response.json()
            msg_id = result.get("data", {}).get("message_id")
            # بعد 10 ثانیه پیام هشدار رو حذف کن
            if msg_id:
                time.sleep(10)
                delete_message(chat_id, msg_id)
        return response.status_code == 200
    except Exception as e:
        print(f"Warning error: {e}")
        return False

# ---------- دریافت پیام ----------
def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    data = {"timeout": 10}
    if offset:
        data["offset"] = offset
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("data", {}).get("updates", [])
        return []
    except Exception as e:
        print(f"Get updates error: {e}")
        return []

# ---------- حلقه اصلی ----------
def main():
    offset = None
    print("🚀 ربات ضد تبلیغ روبیکا فعال شد!")
    print(f"🔒 فقط روی گروه مجاز کار می‌کند")
    print("🤖 هوش مصنوعی اختصاصی آماده است")
    print("-" * 50)

    while True:
        try:
            updates = get_updates(offset)

            for update in updates:
                if "update_id" in update:
                    offset = int(update["update_id"]) + 1

                # فقط گروه مجاز
                chat_id = update.get("chat_id")
                if chat_id != ALLOWED_CHAT_ID:
                    continue

                if update.get("type") == "NewMessage":
                    msg = update.get("new_message", {})
                    message_id = msg.get("message_id")
                    user_guid = msg.get("sender_user_guid")
                    text = msg.get("text", "")

                    if not text:
                        continue

                    # بررسی تخلفات
                    reason = None
                    if has_link(text):
                        reason = "لینک/آدرس اینترنتی"
                    elif has_contact_info(text):
                        reason = "درج آیدی یا اطلاعات تماس"
                    elif has_forwarded_flag(update):
                        reason = "فوروارد از گروه یا کانال دیگر"
                    elif is_ad_content(text):
                        reason = "تشخیص محتوای تبلیغاتی توسط AI"

                    if reason:
                        print(f"🚨 تخلف: {reason} - {text[:50]}...")
                        delete_message(chat_id, message_id)
                        send_warning(chat_id, user_guid, reason)
                    else:
                        # پیام سالم - فقط لاگ کن، جواب نده
                        print(f"✅ پیام سالم: {text[:50]}...")

            time.sleep(1)

        except Exception as e:
            print(f"❌ Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
