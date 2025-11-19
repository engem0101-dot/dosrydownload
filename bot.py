import os
import uuid
import time
import logging
import threading
from flask import Flask, send_file, abort
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import yt_dlp

# ---------------------------
# 🔐 ENV VARIABLES
# ---------------------------

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

# رابط الدومين الخاص بالتحميل
APP_DOMAIN = os.getenv("APP_DOMAIN", "https://dosrydownload.onrender.com")

# مجلد التخزين
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ---------------------------
# 📝 Logging
# ---------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------
# ⚙️ yt-dlp Settings (الأفضل والأكثر استقراراً)
# ---------------------------

def ydl_opts(output_path):
    return {
        # Sorting بدلاً من format لتفادي errors
        "format_sort": ["vcodec:h264", "res", "acodec:aac"],

        "outtmpl": output_path,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,

        # كوكيز يوتيوب
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,

        # تفعيل mweb لضمان PO Token
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "web"]
            }
        },
    }


# ---------------------------
# 🧹 Auto delete
# ---------------------------

def auto_delete(filepath, delay=600):
    """Delete file after 10 minutes"""
    def delete():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"🗑 Deleted: {filepath}")
        except Exception as e:
            logger.error(f"Delete error: {e}")

    t = threading.Timer(delay, delete)
    t.daemon = True
    t.start()


# ---------------------------
# 🤖 Telegram Handlers
# ---------------------------

def start(update, context):
    update.message.reply_text(
        "🎬 *أرسل رابط أي فيديو وسأقوم بتحميله:*\n"
        "• YouTube\n• TikTok (بدون علامة مائية)\n• Instagram\n• Twitter\n• Facebook\n\n"
        "✔ إذا الحجم أقل من 50MB أرسل لك الفيديو مباشر\n"
        "✔ إذا أكبر من 50MB أرسل رابط تحميل مباشر\n",
        parse_mode="Markdown"
    )


def handle_download(update, context):
    url = update.message.text.strip()

    # تخطي أي شيء ليس رابط
    if not (url.startswith("http://") or url.startswith("https://")):
        return

    msg = update.message.reply_text("⏳ جاري التحميل…")

    try:
        file_id = str(uuid.uuid4())
        output_tpl = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

        # Download
        with yt_dlp.YoutubeDL(ydl_opts(output_tpl)) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        size = os.path.getsize(filepath)

        if size <= 50 * 1024 * 1024:
            # Send file directly
            update.message.reply_document(open(filepath, "rb"))
            auto_delete(filepath)
        else:
            # Send download link
            download_url = f"{APP_DOMAIN}/d/{file_id}"
            update.message.reply_text(
                f"📥 **الملف كبير (> 50MB)**\n"
                f"رابط التحميل المباشر:\n{download_url}\n\n"
                "⏰ الرابط صالح لمدة 10 دقائق",
                parse_mode="Markdown"
            )
            auto_delete(filepath)

        msg.delete()

    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ:\n{e}")
        logger.error(e)


# ---------------------------
# 🌐 Flask Server
# ---------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

@app.route("/d/<file_id>")
def download_file(file_id):
    # البحث عن الملف
    search = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(file_id)]
    if not search:
        return abort(404)

    full_path = os.path.join(DOWNLOAD_FOLDER, search[0])
    return send_file(full_path, as_attachment=True)


# ---------------------------
# 🚀 Start Telegram Bot (Polling)
# ---------------------------

def run_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_download))

    updater.start_polling()
    updater.idle()


# ---------------------------
# 🚀 Run Flask + Bot
# ---------------------------

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
