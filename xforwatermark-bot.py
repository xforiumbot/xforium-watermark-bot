import os
from io import BytesIO
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")  # make sure BOT_TOKEN is set in Render environment

# --- Flask keep-alive server ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ xForium Watermark Bot is running!"

# --- Watermark function using image watermark ---
def add_watermark_with_image(original_image):
    # Open the watermark image (make sure 'watermark.png' is in same folder)
    watermark = Image.open("watermark.png").convert("RGBA")

    # Resize watermark to about 40% of original image width (adjust if needed)
    ow, oh = original_image.size
    new_w = int(ow * 0.4)
    aspect_ratio = watermark.height / watermark.width
    new_h = int(new_w * aspect_ratio)
    watermark = watermark.resize((new_w, new_h), Image.LANCZOS)

    # Position: slightly right of center
    pos_x = int(ow * 0.55 - new_w / 2)
    pos_y = int(oh / 2 - new_h / 2)

    # Paste watermark with alpha transparency
    watermarked = original_image.convert("RGBA")
    watermarked.alpha_composite(watermark, (pos_x, pos_y))
    return watermarked.convert("RGB")

# --- Telegram Handlers ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    img_bytes = await photo_file.download_as_bytearray()

    original_image = Image.open(BytesIO(img_bytes))
    watermarked_image = add_watermark_with_image(original_image)

    output = BytesIO()
    watermarked_image.save(output, format='JPEG')
    output.seek(0)

    await update.message.reply_photo(photo=output, caption="✅ Watermark added!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a photo, and I’ll add your @xForium watermark to it!")

# --- Main entry ---
if __name__ == "__main__":
    import threading

    # Run Flask keep-alive in background
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))).start()

    # Start Telegram bot
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Bot is running...")
    app_bot.run_polling()
