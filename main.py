import os
import logging
import tempfile
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokens (Railway env variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# 🎧 Voice function
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    return "output.mp3"

# 🚀 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to Drama Explanation Bot!\n\n"
        "Send me a video and I will explain it in English with voice!\n"
        "Supported: MP4, AVI, MKV (max 100MB)"
    )

# 🎬 Handle video
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        video = update.message.video or update.message.document

        if not video:
            await update.message.reply_text("❌ Please send a valid video file.")
            return

        # ✅ 100MB limit
        if video.file_size > 100 * 1024 * 1024:
            await update.message.reply_text("❌ 100MB se badi file allowed nahi")
            return

        await update.message.reply_text("⏳ Processing video...")

        file = await context.bot.get_file(video.file_id)

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        await update.message.reply_text("🧠 AI is analyzing video...")

        video_file = genai.upload_file(path=tmp_path, mime_type="video/mp4")

        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        prompt = """Watch this video carefully and create a clear, engaging, and dramatic explanation in English only.
Explain the full story in a simple and emotional way like a movie narration."""

        response = model.generate_content([video_file, prompt])

        explanation = response.text

        # 🎧 Voice output
        voice_file = text_to_voice(explanation)
        await update.message.reply_audio(audio=open(voice_file, "rb"))

        # 📩 Text output
        if len(explanation) > 4000:
            parts = [explanation[i:i+4000] for i in range(0, len(explanation), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(explanation)

        os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# 💬 Handle text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send a video — I will explain it with AI + voice!"
    )

# 🏁 Main function
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()

if __name__ == "__main__":
    main()
