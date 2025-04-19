import telebot
import requests
import logging
import time
from concurrent.futures import ThreadPoolExecutor

# === Sozlamalar ===
BOT_TOKEN = "8113086612:AAH1I2ffEr2FQH04PSlpTRr8Rony5DYMd0g"
GEMINI_API_KEY = "AIzaSyCBQ3c-xPQNOy9joKbF9g0_OEzYgPDUVzw"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# === Logger ===
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# === Bot ===
bot = telebot.TeleBot(BOT_TOKEN)

# === Gemini API bilan ishlash ===
def ask_gemini(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        candidates = data.get("candidates", [])
        if not candidates:
            return "⚠️ AI javob bera olmadi. Iltimos, boshqa savol berib ko‘ring."

        # Javobni olish va formatlash
        text = candidates[0]["content"]["parts"][0]["text"]
        return f"🤖 AI javobi:\n\n{text.strip()}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API error: {e}")
        return "❌ So‘rov yuborishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko‘ring."

# === /start komandasi ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Assalomu alaykum!\n\n"
        "Men sun'iy intellekt asosidagi botman.\n"
        "Savolingizni yoki matningizni yozing — men javob beraman. ✨"
    )
    bot.reply_to(message, welcome_text)

# === Matnli so‘rovlar ===
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_user_message(message):
    thinking_msg = bot.reply_to(message, "⏳ Javob tayyorlanmoqda...")

    def process_request():
        reply = ask_gemini(message.text)
        try:
            bot.edit_message_text(
                reply,
                chat_id=message.chat.id,
                message_id=thinking_msg.message_id,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Bot response error: {e}")
            bot.send_message(message.chat.id, reply)

    ThreadPoolExecutor().submit(process_request)

# === Ishga tushirish ===
if __name__ == "__main__":
    logger.info("Bot ishga tushmoqda...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Bot ishlashda xatolik: {e}")
            time.sleep(15)
