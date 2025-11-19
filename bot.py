import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import yt_dlp

# ---------------------------
# 🔐 ENV variables
# ---------------------------
TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)

# ---------------------------
# 🚀 Flask App
# ---------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

@app.route("/healthz")
def health():
    return "OK", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    except Exception as e:
        print("Webhook error:", e)

    return "OK", 200


# ---------------------------
# ⚙️ YDL Options
# ---------------------------
def get_ydl_opts():
    return {
        "format": "best/bestvideo+bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,

        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4"
        }],

        # تمكين mweb client للـ PO Token
        "extractor_args": {
            "youtube": {
                "player_client": "mweb"
            }
        }
    }


# ---------------------------
# 🤖 Handlers
# ---------------------------
def start_cmd(update, context):
    update.message.reply_text(
        "🎬 أهلاً! أرسل أي رابط وسأحمّل لك الفيديو.\n\n"
        "✓ YouTube\n✓ TikTok بدون علامة مائية\n✓ Instagram\n✓ Twitter\n✓ Facebook\n✓ Reddit\n✓ Pinterest"
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
# 🧠 Dispatcher
# ---------------------------
dispatcher = Dispatcher(bot, None, workers=4)
dispatcher.add_handler(CommandHandler("start", start_cmd))
dispatcher.add_handler(MessageHandler(Filters.text, download))


# ---------------------------
# 🚀 Set Webhook once
# ---------------------------
def set_webhook():
    bot.delete_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")
    print("Webhook set →", f"{APP_URL}/{TOKEN}")


# ---------------------------
# 🚀 Run Server
# ---------------------------
if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
