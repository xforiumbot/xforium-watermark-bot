import os
from io import BytesIO
from PIL import Image, ImageEnhance
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import threading

# --- Bot token ---
BOT_TOKEN = "8259315231:AAG_CJPN5XCYbstbA1j-JXw_QQJqTGR_rxs"

# --- Flask app for Render health check ---
server = Flask(__name__)

@server.route('/')
def home():
    return "✅ Watermark bot is running!"

# --- Watermark function ---
def add_watermark(image_stream):
    original = Image.open(image_stream).convert("RGBA")

    # Load watermark image
    watermark = Image.open("watermark.png").convert("RGBA")

    # Resize watermark to ~70% of the original width
    new_width = int(original.width * 0.7)
    aspect_ratio = watermark.height / watermark.width
    new_height = int(new_width * aspect_ratio)
    watermark = watermark.resize((new_width, new_height), Image.LANCZOS)

    # Rotate watermark 15 degrees
    watermark = watermark.rotate(15, expand=1)

    # Adjust opacity (~95%)
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.95)
    watermark.putalpha(alpha)

    # Position: center vertically, slightly right
    x = int(original.width * 0.62 - watermark.width / 2)
    y = int(original.height / 2 - watermark.height / 2)

    # Combine watermark with original
    watermarked = Image.new("RGBA", original.size)
    watermarked.paste(original, (0, 0))
    watermarked.paste(watermark, (x, y), watermark)

    return watermarked.convert("RGB")

# --- Telegram handler ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    image_bytes = BytesIO()
    await photo_file.download_to_memory(out=image_bytes)
    image_bytes.seek(0)

    result = add_watermark(image_bytes)
    output = BytesIO()
    result.save(output, format="JPEG")
    output.seek(0)

    await update.message.reply_photo(photo=output, caption="✅ Watermark added successfully!")

# --- Run bot + server together ---
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    # Run Telegram bot in a thread
    threading.Thread(target=run_bot, daemon=True).start()

    # Run Flask server for Render
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)
