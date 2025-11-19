import os
import yt_dlp
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = os.environ.get("BOT_TOKEN")  # التوكن من Render

# إعداد yt-dlp لتجاوز PO Token
def get_ydl_opts(output):
    return {
        "outtmpl": output,
        "merge_output_format": "mp4",
        "format": "bestvideo+bestaudio/best",
        "extractor_args": {
            "youtube": {
                "player_client": "mweb",          # نستخدم mweb client
                "po_token_provider": "bgutil"     # تفعيل PO Token Provider
            }
        }
    }

def start(update, context):
    update.message.reply_text(
        "🎥 *YouTube Download Bot*\n\n"
        "أرسل رابط فيديو من:\n"
        "- YouTube\n- TikTok\n- Instagram\n- Twitter\n- Shorts\n\n"
        "🔥 سيتم التحميل بأعلى جودة تلقائيًا.\n\n"
        "🎧 لتحميل صوت فقط (MP3):\n"
        "`mp3 <الرابط>`",
        parse_mode="Markdown"
    )

def download_video(update, context):
    url = update.message.text.strip()

    if not url.startswith("http"):
        update.message.reply_text("❌ هذا ليس رابطًا صالحًا.", parse_mode="Markdown")
        return

    update.message.reply_text("⏳ *جاري تحميل الفيديو…*", parse_mode="Markdown")

    try:
        opts = get_ydl_opts("video.%(ext)s")
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        file = [f for f in os.listdir(".") if f.startswith("video")][0]

        update.message.reply_video(
            open(file, "rb"),
            caption="✔️ *تم التحميل!*",
            parse_mode="Markdown"
        )

        os.remove(file)

    except Exception as e:
        update.message.reply_text(f"❌ *حدث خطأ أثناء التحميل:*\n`{e}`", parse_mode="Markdown")


def download_mp3(update, context):
    parts = update.message.text.split()
    if len(parts) < 2:
        update.message.reply_text("❌ استخدم:\n`mp3 <الرابط>`", parse_mode="Markdown")
        return

    url = parts[1]
    update.message.reply_text("🎧 *جاري تحويل الصوت إلى MP3…*", parse_mode="Markdown")

    try:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": "audio.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "extractor_args": {
                "youtube": {
                    "player_client": "mweb",
                    "po_token_provider": "bgutil"
                }
            }
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        file = [f for f in os.listdir(".") if f.startswith("audio")][0]

        update.message.reply_audio(
            open(file, "rb"),
            caption="🎧 *تم استخراج الصوت بنجاح!*",
            parse_mode="Markdown"
        )

        os.remove(file)

    except Exception as e:
        update.message.reply_text(f"❌ *حدث خطأ أثناء التحويل:*\n`{e}`", parse_mode="Markdown")


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
