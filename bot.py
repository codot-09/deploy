import telebot
import requests
import time
import os
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import logging
from pathlib import Path

API_KEY = "06a735a0-4d0f-425d-9655-1ba8728e96ab"
BASE_URL = "https://apihut.in/api/download/videos"
BOT_TOKEN = "7567730285:AAGm3RDt_mdOC5H5VnfiEPjL6OZx0wsm214"
MAX_REQUESTS_PER_MINUTE = 5
TEMP_DIR = Path("/tmp/videos")  # Render server uchun /tmp ishlatiladi

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

USER_REQUESTS = {}
REQUEST_LOCK = Lock()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
executor = ThreadPoolExecutor(max_workers=5)

class VideoDownloadError(Exception):
    pass

def ensure_temp_dir():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def check_rate_limit(user_id: int) -> bool:
    with REQUEST_LOCK:
        current_time = time.time()
        USER_REQUESTS[user_id] = [
            t for t in USER_REQUESTS.get(user_id, [])
            if current_time - t < 60
        ]
        if len(USER_REQUESTS[user_id]) < MAX_REQUESTS_PER_MINUTE:
            USER_REQUESTS[user_id].append(current_time)
            return True
        return False

def download_video_api(video_url: str, user_id: int) -> Optional[str]:
    headers = {
        'x-avatar-key': API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        "video_url": video_url,
        "type": "instagram",
        "user_id": str(user_id)
    }
    
    for attempt in range(3):
        try:
            response = requests.post(BASE_URL, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") == 1 and "data" in data and data["data"]:
                return data["data"][0]["url"]
            return None
            
        except (requests.RequestException, ValueError) as e:
            logger.error(f"API attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
            continue
    return None

def download_and_send_video(download_url: str, chat_id: int) -> None:
    temp_file = TEMP_DIR / f"video_{chat_id}_{int(time.time())}.mp4"
    
    try:
        with requests.get(download_url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        with open(temp_file, 'rb') as video:
            bot.send_video(
                chat_id,
                video,
                caption="🌟 @vd_downloadbot orqali siz uchun yuklandi!",
                supports_streaming=True,
                timeout=30
            )
            
    except (requests.RequestException, telebot.apihelper.ApiException) as e:
        logger.error(f"Video processing error: {e}")
        bot.send_message(
            chat_id,
            "😔 Kechirasiz, videoni yuklashda muammo yuz berdi. Keyinroq urinib ko‘ring!"
        )
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError as e:
                logger.error(f"File removal error: {e}")

def process_video_request(message: telebot.types.Message) -> None:
    chat_id = message.chat.id
    video_url = message.text.strip()
    
    if 'instagram.com' not in video_url:
        bot.reply_to(
            message,
            "🤔 Faqat Instagram videolarini yuklay olaman! Iltimos, Instagram URL yuboring."
        )
        return
    
    if not check_rate_limit(chat_id):
        bot.reply_to(
            message,
            "⏳ Bir daqiqada 5 tadan ortiq so‘rov yuborish mumkin emas. Biroz kuting!"
        )
        return
    
    status_msg = bot.reply_to(message, "✨ Video yuklanmoqda, biroz sabr qiling...")
    
    download_url = download_video_api(video_url, chat_id)
    if not download_url:
        bot.edit_message_text(
            "😕 Afsus, bu videoni yuklab ololmadim. URL to‘g‘ri ekanligini tekshiring!",
            chat_id,
            status_msg.message_id
        )
        return
    
    executor.submit(download_and_send_video, download_url, chat_id)
    bot.delete_message(chat_id, status_msg.message_id)

@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message) -> None:
    welcome_text = (
        "🌸 Salom! Instagram video yuklovchi botga xush kelibsiz!\n"
        "Instagram’dan video yuklash uchun faqat URL ni yuboring.\n\n"
        "<b>Misol:</b>\n"
        "https://www.instagram.com/reel/example/\n\n"
        "🎉 Tez va oson yuklab oling!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message: telebot.types.Message) -> None:
    process_video_request(message)

def main():
    ensure_temp_dir()
    logger.info("Bot serverda ishga tushdi")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()