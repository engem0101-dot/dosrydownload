import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import yt_dlp

# ============================
#   إعدادات عامة
# ============================
TOKEN = os.getenv("BOT_TOKEN")  # ضع التوكن في Render Environment
COOKIES_PATH = "cookies.txt"    # بدون مجلدات

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================
#   إعداد yt-dlp مع Cookies
# ============================
def get_ydl_opts():
    return {
        "outtmpl": "%(title)s.%(ext)s",
        "cookies": COOKIES_PATH,
        "format": "best",
        "noprogress": True,
        "quiet": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": "mweb",
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
        }
    }


# ============================
#   الدوال الأساسية
# ============================
def start(update, context):
    update.message.reply_text("أرسل رابط الفيديو لتحميله 🎬")


def download(update, context):
    url = update.message.text.strip()

    update.message.reply_chat_action(ChatAction.TYPING)
    update.message.reply_text("⏳ جاري معالجة الرابط...")

    try:
        ydl_opts = get_ydl_opts()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        update.message.reply_document(open(filename, "rb"))
    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ: {e}")


# ============================
#   تشغيل Webhook في Render
# ============================
def main():
    PORT = int(os.environ.get("PORT", 8080))
    APP_URL = os.environ.get("APP_URL")  # مثال: https://yourbot.onrender.com

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download))

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{APP_URL}/{TOKEN}",
    )

    updater.idle()


if __name__ == "__main__":
    main()
