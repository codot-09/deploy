import requests
import time

TOKEN = "7500957342:AAGfIfIl_Y-C_x15FKXyVUgThWja7mMC2Ig"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    res = requests.get(url, params=params)
    return res.json()["result"]

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

def get_usd_rate():
    try:
        res = requests.get(CBU_URL)
        for item in res.json():
            if item["Ccy"] == "USD":
                return float(item["Rate"])
    except:
        return None

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").lower().strip()

    if text == "/start":
        send_message(chat_id, "💱 Valyuta konvertoriga xush kelibsiz!\n\nMasalan: `100 usd` yoki `150000 uzs`")
        return

    parts = text.split()
    if len(parts) != 2 or not parts[0].replace('.', '', 1).isdigit():
        send_message(chat_id, "❗ Format noto‘g‘ri. Masalan: `100 usd` yoki `150000 uzs`")
        return

    amount = float(parts[0])
    currency = parts[1]
    rate = get_usd_rate()
    if not rate:
        send_message(chat_id, "❗ Valyuta kursini olishda xatolik.")
        return

    if currency == "usd":
        result = amount * rate
        send_message(chat_id, f"{amount} USD ≈ {round(result, 2):,} UZS")
    elif currency == "uzs":
        result = amount / rate
        send_message(chat_id, f"{amount:,} UZS ≈ {round(result, 2)} USD")
    else:
        send_message(chat_id, "❗ Faqat `usd` va `uzs` valutalari qo‘llab-quvvatlanadi.")

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update:
                handle_message(update["message"])
        time.sleep(1)

if __name__ == "__main__":
    main()
