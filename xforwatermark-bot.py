import os
import threading
import asyncio
from io import BytesIO
from PIL import Image, ImageEnhance
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# --- Bot token ---
BOT_TOKEN = "8259315231:AAG_CJPN5XCYbstbA1j-JXw_QQJqTGR_rxs"

# --- Flask app for Render ---
server = Flask(__name__)

@server.route('/')
def home():
    return "✅ xForium Watermark Bot is running!"

# --- Watermark function ---
def add_watermark(image_stream, opacity=0.5):
    """
    image_stream: BytesIO object
    opacity: float between 0.0 (transparent) to 1.0 (fully visible)
    """
    original = Image.open(image_stream).convert("RGBA")
    watermark = Image.open("watermark.png").convert("RGBA")

    # Resize watermark ~80% of original width
    new_width = int(original.width * 0.8)
    aspect_ratio = watermark.height / watermark.width
    new_height = int(new_width * aspect_ratio)
    watermark = watermark.resize((new_width, new_height), Image.LANCZOS)

    # Rotate watermark ~15°
    watermark = watermark.rotate(15, expand=1)

    # Adjust opacity
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    watermark.putalpha(alpha)

    # Position: centered vertically, slightly to the right
    x = int(original.width * 0.6 - watermark.width / 2)
    y = int(original.height / 2 - watermark.height / 2)

    # Paste watermark on image
    watermarked = Image.new("RGBA", original.size)
    watermarked.paste(original, (0, 0))
    watermarked.paste(watermark, (x, y), watermark)
    return watermarked.convert("RGB")

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me any photo and I'll watermark it for you!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    image_bytes = BytesIO()
    await photo_file.download_to_memory(out=image_bytes)
    image_bytes.seek(0)

    # Run blocking watermark code in a thread
    result = await asyncio.to_thread(add_watermark, image_bytes, 0.5)  # adjust opacity here (0.0-1.0)

    output = BytesIO()
    result.save(output, format="JPEG")
    output.seek(0)

    await update.message.reply_photo(photo=output, caption="✅ Watermark added successfully!")

# --- Start bot ---
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🚀 Telegram bot polling started...")
    app.run_polling()

if __name__ == "__main__":
    # Start Flask in a thread (Render requirement)
    threading.Thread(target=lambda: server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080))), daemon=True).start()

    # Run Telegram bot (main thread)
    run_bot()
