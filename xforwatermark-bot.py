import logging
import os
import threading
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

# Flask app to keep the bot alive on Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Watermark Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# -------------------------------
# Watermark function
# -------------------------------
def add_watermark(image: Image.Image) -> Image.Image:
    watermark_text = "@xforium"

    # Convert image to RGBA for transparency
    image = image.convert("RGBA")
    width, height = image.size

    # Create transparent layer for the watermark
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Calculate font size ~6% of width (big & bold watermark)
    font_size = int(width * 0.06)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    # Measure text size and position
    text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Position: centered vertically, slightly right horizontally
    x = (width - text_width) // 2 + int(width * 0.15)
    y = (height - text_height) // 2

    # Create a rotated watermark image
    watermark_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    watermark_draw = ImageDraw.Draw(watermark_layer)

    # Draw semi-transparent white text
    watermark_draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 64))  # 64 ≈ 25% opacity

    # Rotate ~15°
    rotated_watermark = watermark_layer.rotate(15, expand=1)

    # Combine original image with watermark
    combined = Image.alpha_composite(image, rotated_watermark)

    return combined.convert("RGB")

# -------------------------------
# Telegram Bot Handlers
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me any image and I’ll watermark it with @xforium!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO()
    await photo_file.download_to_memory(photo_bytes)
    photo_bytes.seek(0)

    # Open and watermark the image
    original_image = Image.open(photo_bytes)
    watermarked_image = add_watermark(original_image)

    # Send back to user
    output_bytes = BytesIO()
    watermarked_image.save(output_bytes, format='JPEG')
    output_bytes.seek(0)

    await update.message.reply_photo(photo=output_bytes, caption="✅ Watermarked!")

# -------------------------------
# Main function
# -------------------------------
def main():
    if TOKEN is None:
        logger.error("BOT_TOKEN not found in environment variables!")
        return

    # Start Flask server in a separate thread
    threading.Thread(target=run_flask).start()

    # Initialize bot
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
