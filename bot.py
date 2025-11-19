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

# دومين التطبيق (لتوليد روابط التحميل)
APP_DOMAIN = os.getenv("APP_DOMAIN", "https://dosrydownload.onrender.com")

# مجلد التحميلات
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ---------------------------
# 📝 Logging
# ---------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# ⚙️ yt-dlp Settings
# ---------------------------

def ydl_opts(output_path):
    return {
        "format": "best/bestvideo+bestaudio/best",
        "outtmpl": output_path,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "web"]
            }
        }
    }

# ---------------------------
# 🧹 Auto-delete files
# ---------------------------

def auto_delete(filepath, delay=600):
    """يحذف الملفات بعد 10 دقائق"""
    def delete():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"🗑️ Deleted: {filepath}")
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
        "🎬 أهلاً! أرسل رابط فيديو وسأقوم بتحميله:\n"
        "• YouTube\n• TikTok\n• Instagram\n• Twitter\n• Facebook\n"
        "✔ إذا الحجم أقل من 50MB سيتم إرساله مباشرة\n"
        "✔ إذا أكبر سأرسل لك رابط تحميل مباشر"
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

        with yt_dlp.YoutubeDL(ydl_opts(output_tpl)) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        size = os.path.getsize(filepath)

        if size <= 50 * 1024 * 1024:
            # √ الملف صغير → أرسله مباشرة
            update.message.reply_video(open(filepath, "rb"))
            auto_delete(filepath)
        else:
            # √ الملف كبير → رابط تحميل مباشر
            download_url = f"{APP_DOMAIN}/d/{file_id}"
            update.message.reply_text(
                f"🔗 **ملف كبير > 50MB**\n"
                f"رابط التحميل:\n{download_url}\n\n"
                "⏰ الرابط صالح لمدة 10 دقائق"
            )
            auto_delete(filepath)

        msg.delete()

    except Exception as e:
        logger.error(e)
        update.message.reply_text(f"❌ خطأ أثناء التحميل:\n{e}")

# ---------------------------
# 🌐 Flask Server
# ---------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

@app.route("/d/<file_id>")
def download_file(file_id):
    search = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(file_id)]
    if not search:
        return abort(404)

    full_path = os.path.join(DOWNLOAD_FOLDER, search[0])
    return send_file(full_path, as_attachment=True)

# ---------------------------
# 🚀 Start POLLING (بدون Webhook)
# ---------------------------

def run_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_download))

    updater.start_polling()
    updater.idle()

# ---------------------------
# 🚀 Run Flask + Bot together
# ---------------------------

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
