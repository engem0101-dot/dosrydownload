import os
import logging
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import yt_dlp

# ---------------------------
# 🚀 Flask server (Render)
# ---------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

@app.route("/healthz")
def health():
    return "OK", 200


# ---------------------------
# 🔐 ENV variables
# ---------------------------
TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)


# ---------------------------
# ⚙️ YDL Options — Multi-platform
# ---------------------------
def get_ydl_opts():
    return {
        "format": "best/bestvideo+bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,

        # كوكيز لليوتيوب (إن وجدت)
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,

        # TikTok بدون علامة مائية
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4"
        }],

        # دعم PO Token تلقائي ليوتيوب
        "extractor_args": {
            "youtube": {
                "player_client": "mweb"
            }
        },
    }


# ---------------------------
# 🤖 Telegram Bot Handlers
# ---------------------------
def start_cmd(update, context):
    update.message.reply_text(
        "🎬 مرحباً! أرسل أي رابط وسيتم تحميل الفيديو بأعلى جودة.\n\n"
        "✓ YouTube\n✓ TikTok بدون علامة مائية\n✓ Instagram\n✓ Twitter (X)\n✓ Facebook\n✓ Reddit\n✓ Pinterest\nوغيرها…"
    )


def download(update, context):
    url = update.message.text.strip()
    update.message.reply_text("⏳ جاري التحميل…")

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        update.message.reply_document(open(filename, "rb"))

    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ:\n{e}")


# ---------------------------
# 🚀 Webhook + Flask Runner
# ---------------------------
def start_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(MessageHandler(Filters.text, download))

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{APP_URL}/{TOKEN}",
    )

    updater.idle()


if __name__ == "__main__":
    import threading
    threading.Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=PORT)
