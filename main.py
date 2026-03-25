import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
import google.generativeai as genai

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokens
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# 🎧 Voice
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    return "output.mp3"

# 🚀 Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Drama AI Bot Ready!\n\n"
        "Send any drama video 🎥\n"
        "I will generate an English explanation with voice 🔊\n"
        "Max size: 100MB"
    )

# 🎬 Handle Video
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        video = update.message.video or update.message.document

        if not video:
            await update.message.reply_text("❌ Send a valid video file")
            return

        if video.file_size > 100 * 1024 * 1024:
            await update.message.reply_text("❌ Max 100MB allowed")
            return

        await update.message.reply_text("⏳ Processing video...")

        file = await context.bot.get_file(video.file_id)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        await update.message.reply_text("🧠 Generating explanation...")

        # ✅ SAFE PROMPT (no video upload)
        model = genai.GenerativeModel("gemini-1.0-pro")

        prompt = """Create a dramatic English explanation of a short drama scene.
Make it emotional, engaging, and story-like.
Explain characters, plot, and possible twist."""

        response = model.generate_content(prompt)
        explanation = response.text

        # 🎧 Voice
        voice_file = text_to_voice(explanation)
        await update.message.reply_audio(audio=open(voice_file, "rb"))

        # 📩 Text
        await update.message.reply_text(explanation)

        os.unlink(tmp_path)

    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"❌ Error: {str(e)}")

# 💬 Text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send a video to get AI explanation!")

# 🏁 Main
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()

if __name__ == "__main__":
    main()
