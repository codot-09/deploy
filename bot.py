import telebot
import requests
import time
import os
import logging
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Sozlashlar
BOT_TOKEN = "7897693976:AAEpm78aPN8e2JS9_UGR7s0Ch81jqYYO2XE"
API_KEY = "46aae578-102d-422c-911c-5d6d4a70fa84"
BASE_URL = "https://apihut.in/api/download/videos"
TEMP_DIR = Path("/home/codot09/video_bot/videos")  # Serverdagi yo'nalish
TEMP_DIR.mkdir(exist_ok=True, parents=True)  # Katalogni yaratish


# Botni ishga tushirish
bot = telebot.TeleBot(BOT_TOKEN)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Yuklovchi funksiyalar
def download_video(url: str, chat_id: int) -> Optional[str]:
    try:
        headers = {'x-avatar-key': API_KEY}
        payload = {"video_url": url, "type": "instagram"}
        
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success') and data.get('data'):
            return data['data'][0]['url']
        return None
        
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return None

def save_video(url: str, chat_id: int) -> Optional[str]:
    try:
        temp_file = TEMP_DIR / f"{chat_id}_{int(time.time())}.mp4"  # Lokallashtirilgan fayl yo'nalishi
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return temp_file  # Faylning to'liq yo'nalishini qaytarish
    except Exception as e:
        logger.error(f"Video save failed: {e}")
        return None


# Bot handlerlari
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🎬 Instagram Video Yuklovchi Bot\n\n"
        "Instagram reels/video linkini yuboring:\n"
        "Misol: https://www.instagram.com/reel/Cxample..."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda m: True)
def handle_video_request(message):
    if 'instagram.com' not in message.text:
        bot.reply_to(message, "❌ Faqat Instagram linklari qabul qilinadi!")
        return

    processing_msg = bot.reply_to(message, "⏳ Video yuklanmoqda...")

    def process_request():
        try:
            video_url = download_video(message.text, message.chat.id)
            if not video_url:
                raise Exception("Video URL not found")
            
            video_path = save_video(video_url, message.chat.id)
            if not video_path:
                raise Exception("Failed to save video")
            
            with open(video_path, 'rb') as video_file:
                bot.send_video(
                    message.chat.id,
                    video_file,
                    caption="📥 @VideoDownloaderBot orqali yuklandi",
                    supports_streaming=True
                )
            
            os.remove(video_path)
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            bot.edit_message_text(
                "❌ Yuklash muvaffaqiyatsiz tugadi. Qayta urunib ko'ring.",
                message.chat.id,
                processing_msg.message_id
            )

    ThreadPoolExecutor().submit(process_request)


# Ishga tushirish
if __name__ == "__main__":
    logger.info("Bot ishga tushmoqda...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            time.sleep(15)
