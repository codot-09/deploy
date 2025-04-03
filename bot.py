import telebot
import requests
import time
import os
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging

bot = telebot.TeleBot("7897693976:AAEpm78aPN8e2JS9_UGR7s0Ch81jqYYO2XE", parse_mode='HTML')
executor = ThreadPoolExecutor(max_workers=5)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TEMP_DIR = Path("/home/yourusername/video_bot/videos")
TEMP_DIR.mkdir(exist_ok=True)

def download_video(url, chat_id):
    try:
        temp_file = TEMP_DIR / f"{chat_id}_{int(time.time())}.mp4"
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return temp_file
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Instagram video yuklovchi botga xush kelibsiz!\nVideo linkini yuboring.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if 'instagram.com' not in message.text:
        bot.reply_to(message, "Faqat Instagram linklari qabul qilinadi!")
        return

    msg = bot.reply_to(message, "Video yuklanmoqda...")
    
    def process_video():
        try:
            video_url = f"https://apihut.in/api/download/videos?video_url={message.text}"
            response = requests.get(video_url, headers={'x-avatar-key': "46aae578-102d-422c-911c-5d6d4a70fa84"}, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and data.get('data'):
                video_file = download_video(data['data'][0]['url'], message.chat.id)
                if video_file:
                    with open(video_file, 'rb') as video:
                        bot.send_video(message.chat.id, video)
                    os.remove(video_file)
                    bot.delete_message(message.chat.id, msg.message_id)
                    return
        
        except Exception as e:
            logger.error(f"Error: {e}")
        
        bot.edit_message_text("Xatolik yuz berdi!", message.chat.id, msg.message_id)

    executor.submit(process_video)

if __name__ == "__main__":
    logger.info("Bot ishga tushmoqda...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(15)
