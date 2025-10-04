import os
import threading
from io import BytesIO
from PIL import Image, ImageEnhance
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8259315231:AAG_CJPN5XCYbstbA1j-JXw_QQJqTGR_rxs"
server = Flask(__name__)

@server.route('/')
def home():
    return "✅ Watermark bot is running on Render!"

def add_watermark(image_stream):
    original = Image.open(image_stream).convert("RGBA")
    watermark = Image.open("watermark.png").convert("RGBA")

    new_width = int(original.width * 0.5)
    aspect_ratio = watermark.height / watermark.width
    new_height = int(new_width * aspect_ratio)
    watermark = watermark.resize((new_width, new_height), Image.LANCZOS)

    watermark = watermark.rotate(12, expand=True)
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.85)
    watermark.putalpha(alpha)

    x = int(original.width * 0.6 - watermark.width / 2)
    y = int(original.height / 2 - watermark.height / 2)

    watermarked = Image.new("RGBA", original.size)
    watermarked.paste(original, (0, 0))
    watermarked.paste(watermark, (x, y), watermark)
    return watermarked.convert("RGB")

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

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    # Start the bot in a background thread
    threading.Thread(target=run_bot, daemon=True).start()

    # Start the Flask server (this keeps the Render port alive)
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)
