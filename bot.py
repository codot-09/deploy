import telebot
import requests
import time
import os
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import logging
from pathlib import Path

# Sozlamalar
API_KEY = "1348c1b6-f5e0-414a-8d4c-585c95c92e59"
BASE_URL = "https://apihut.in/api/download/videos"
BOT_TOKEN = "7567730285:AAGm3RDt_mdOC5H5VnfiEPjL6OZx0wsm214"
MAX_REQUESTS_PER_MINUTE = 5
TEMP_DIR = Path("videos")  # Joriy papkada videos papkasini yaratadi

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global o'zgaruvchilar
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
    
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 403:
            logger.error("API access forbidden - check API key")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") == 1 and "data" in data and data["data"]:
            return data["data"][0]["url"]
            
        logger.error(f"API response error: {data}")
        return None
        
    except requests.Timeout:
        logger.error("API request timed out")
        return None
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON decode error: {e}")
        return None

def download_and_send_video(download_url: str, chat_id: int) -> None:
    temp_file = TEMP_DIR / f"video_{chat_id}_{int(time.time())}.mp4"
    
    try:
        with requests.get(download_url, stream=True, timeout=20) as r:
            if r.status_code != 200:
                raise VideoDownloadError(f"Download failed with status {r.status_code}")
                
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        with open(temp_file, 'rb') as video:
            bot.send_video(
                chat_id,
                video,
                caption="Video @vd_downloadbot orqali yuklandi",
                supports_streaming=True,
                timeout=30
            )
            
    except requests.RequestException as e:
        logger.error(f"Download error: {e}")
        bot.send_message(
            chat_id,
            "Videoni yuklashda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring."
        )
    except telebot.apihelper.ApiException as e:
        logger.error(f"Telegram API error: {e}")
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError as e:
                logger.error(f"File cleanup error: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Instagram video yuklovchi botga xush kelibsiz.\n"
        "Instagram'dan video yuklash uchun video linkini yuboring.\n\n"
        "Misol: https://www.instagram.com/reel/example/"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    video_url = message.text.strip()
    
    if 'instagram.com' not in video_url:
        bot.reply_to(
            message,
            "Faqat Instagram videolarini yuklash mumkin. Iltimos, Instagram linkini yuboring."
        )
        return
    
    if not check_rate_limit(chat_id):
        bot.reply_to(
            message,
            "So'rovlar soni chegaralangan. Iltimos, bir daqiqadan keyin urunib ko'ring."
        )
        return
    
    status_msg = bot.reply_to(message, "Video yuklanmoqda...")
    
    download_url = download_video_api(video_url, chat_id)
    if not download_url:
        bot.edit_message_text(
            "Videoni yuklab bo'lmadi. Linkni tekshirib, qayta urunib ko'ring.",
            chat_id=chat_id,
            message_id=status_msg.message_id
        )
        return
    
    executor.submit(download_and_send_video, download_url, chat_id)
    bot.delete_message(chat_id, status_msg.message_id)

def run_bot():
    ensure_temp_dir()
    logger.info("Bot ishga tushirilmoqda...")
    
    try:
        # Webhook ni o'chirib, polling ishga tushirish
        bot.remove_webhook()
        time.sleep(1)
        
        logger.info("Polling rejimida ishga tushirilmoqda")
        bot.infinity_polling()
            
    except Exception as e:
        logger.error(f"Bot xatosi: {e}")
        time.sleep(5)
        run_bot()

if __name__ == "__main__":
    run_bot()
