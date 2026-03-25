import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Drama Explanation Bot mein aapka swagat hai!\n\n"
        "Video bhejiye aur main uski poori explanation dunga!\n"
        "Supported: MP4, AVI, MKV (max 20MB)"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Video mil gayi! Processing ho rahi hai, thoda wait karo...")
    
    try:
        video = update.message.video or update.message.document
        file = await context.bot.get_file(video.file_id)
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name
        
        await update.message.reply_text("🧠 Gemini AI video dekh raha hai...")
        
        video_file = genai.upload_file(path=tmp_path, mime_type="video/mp4")
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = """Is video ko dhyan se dekho aur Hindi mein ek dramatic explanation likho jaise ek 
        professional storyteller bata raha ho. Yeh include karo:
        
        🎬 STORY KI SHURUAAT
        - Scene setting kya hai
        - Main characters kaun hain
        
        📖 MAIN PLOT
        - Kya ho raha hai scene mein
        - Important dialogues ya moments
        - Drama aur tension ke points
        
        💥 CLIMAX / TWIST
        - Important turning points
        - Emotional moments
        
        🎭 OVERALL VIBE
        - Is episode ka mood
        - Aage kya ho sakta hai
        
        Engaging aur dramatic style mein likho!"""
        
        response = model.generate_content([video_file, prompt])
        
        explanation = response.text
        
        if len(explanation) > 4000:
            parts = [explanation[i:i+4000] for i in range(0, len(explanation), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(explanation)
            
        os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error aa gaya: {str(e)}\n\nDobara try karo!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Bhai video bhejo — main explanation dunga!\n"
        "Text se kaam nahi chalega, video chahiye! 😄"
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
