import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import yt_dlp

# Load ENV variables
TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)

def get_ydl_opts():
    return {
        "outtmpl": "%(title)s.%(ext)s",
        "format": "best",
        "cookiefile": "cookies.txt",
        "cookies": "cookies.txt",
        "extractor_args": {
            "youtube": {
                "player_client": "mweb",
            }
        },
        "quiet": True,
        "noprogress": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
        }
    }

def start(update, context):
    update.message.reply_text("أرسل رابط يوتيوب لتحميله 🎥")

def download(update, context):
    url = update.message.text.strip()
    update.message.reply_chat_action(ChatAction.TYPING)
    update.message.reply_text("⏳ جاري التحميل...")

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        update.message.reply_document(open(filename, "rb"))
    except Exception as e:
        update.message.reply_text(f"❌ خطأ: {e}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, download))

    # Start webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{APP_URL}/{TOKEN}",
    )

    updater.idle()

if __name__ == "__main__":
    main()
