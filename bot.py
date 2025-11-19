import os
import yt_dlp
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# نقرأ التوكن من Environment Variable داخل Render
TOKEN = os.environ.get("BOT_TOKEN")

def start(update, context):
    update.message.reply_text(
        "🎥 *Download Bot Ready!*\n\n"
        "أرسل رابط لأي فيديو (يوتيوب / تيكتوك / انستا / تويتر / شورتس)\n"
        "وسأحمّله لك بأعلى جودة تلقائيًا 🔥 (1080p – 4K)\n\n"
        "🎧 لتحميل صوت فقط MP3:\n"
        "`mp3 <الرابط>`",
        parse_mode="Markdown"
    )

def download_video(update, context):
    url = update.message.text.strip()

    if not url.startswith("http"):
        update.message.reply_text("❌ *هذا ليس رابطًا صالحًا!*", parse_mode="Markdown")
        return

    update.message.reply_text("⏳ *جاري التحميل…*", parse_mode="Markdown")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio/best",
        "outtmpl": "video.%(ext)s",
        "merge_output_format": "mp4"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # ابحث عن الملف الناتج
        file = [f for f in os.listdir(".") if f.startswith("video")][0]

        update.message.reply_video(
            open(file, "rb"),
            caption="✔️ *تم التحميل بنجاح!*",
            parse_mode="Markdown"
        )

        os.remove(file)

    except Exception as e:
        update.message.reply_text(f"❌ *خطأ أثناء التحميل:*\n`{str(e)}`", parse_mode="Markdown")

def download_mp3(update, context):
    parts = update.message.text.split()
    if len(parts) < 2:
        update.message.reply_text("❌ استخدم:\n`mp3 <الرابط>`", parse_mode="Markdown")
        return

    url = parts[1]
    update.message.reply_text("🎧 *جاري تحويل الصوت…*", parse_mode="Markdown")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "audio.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file = [f for f in os.listdir(".") if f.startswith("audio")][0]

        update.message.reply_audio(
            open(file, "rb"),
            caption="🎧 *تم استخراج الصوت MP3!*",
            parse_mode="Markdown"
        )

        os.remove(file)

    except Exception as e:
        update.message.reply_text(f"❌ *خطأ أثناء التحويل:*\n`{str(e)}`", parse_mode="Markdown")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex(r'^mp3 '), download_mp3))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
