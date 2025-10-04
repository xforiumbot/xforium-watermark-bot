import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment
TOKEN = os.getenv('BOT_TOKEN')

# Flask app for Render port requirement
app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Bot is running!', 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send an image to watermark with @xforium!')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get photo
        photo = await update.message.photo[-1].get_file()
        photo_bytes = await photo.download_as_bytearray()

        # Open image
        img = Image.open(BytesIO(photo_bytes)).convert('RGBA')
        width, height = img.size

        # Watermark settings
        watermark_text = '@xforium'
        font_size = int(width * 0.12)  # 12% of image width → much bigger
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Get text size
        dummy_draw = ImageDraw.Draw(img)
        bbox = dummy_draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Transparent overlay
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Position: centered but shifted slightly right
        x = (width - text_width) // 2 + int(width * 0.1)   # push right 10% of width
        y = (height - text_height) // 2

        # Draw text with stronger opacity (160 = ~63%)
        overlay_draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 160))

        # Rotate overlay
        rotated = overlay.rotate(-15, expand=False)

        # Composite onto original
        img = Image.alpha_composite(img, rotated)

        # Save as JPEG
        bio = BytesIO()
        bio.name = 'watermarked.jpg'
        img_rgb = img.convert('RGB')
        img_rgb.save(bio, 'JPEG')
        bio.seek(0)

        # Send back
        await update.message.reply_photo(photo=bio)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Error processing image. Try another!")

def run_bot():
    if not TOKEN:
        raise ValueError("BOT_TOKEN not set")
    telegram_app = Application.builder().token(TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    telegram_app.run_polling()

if __name__ == '__main__':
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080))))
    flask_thread.daemon = True
    flask_thread.start()
    run_bot()
