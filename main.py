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

        # 🎧 Voice generate
        voice_file = text_to_voice(explanation)
        await update.message.reply_audio(audio=open(voice_file, "rb"))

        # 📩 Text send
        if len(explanation) > 4000:
            parts = [explanation[i:i+4000] for i in range(0, len(explanation), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(explanation)

        os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error aa gaya: {str(e)}")
