import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
TOKEN = os.getenv('BOT_TOKEN')

# Flask app (keeps service alive on Render)
app = Flask(__name__)

@app.route('/')
def health_check():
    return '✅ Bot is running!', 200

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me an image and I'll watermark it with @xforium!")

# Handle photos and add watermark
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download photo
        photo = await update.message.photo[-1].get_file()
        photo_bytes = await photo.download_as_bytearray()

        # Open image
        img = Image.open(BytesIO(photo_bytes)).convert('RGBA')
        width, height = img.size

        # Watermark settings
        watermark_text = "@xforium"
        font_size = int(height * 0.12)  # Adjust watermark size (~12% of image height)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Create transparent overlay
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Calculate text size and position (center)
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw watermark with 30% opacity
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 77))

        # Rotate overlay with expand=True (prevents watermark from disappearing)
        rotated_overlay = overlay.rotate(-15, expand=True)

        # Re-center rotated overlay onto original image size
        final_overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        ox = (final_overlay.width - rotated_overlay.width) // 2
        oy = (final_overlay.height - rotated_overlay.height) // 2
        final_overlay.paste(rotated_overlay, (ox, oy), rotated_overlay)

        # Combine original image with watermark
        watermarked = Image.alpha_composite(img, final_overlay)

        # Save and send result
        bio = BytesIO()
        bio.name = 'watermarked.jpg'
        watermarked.convert("RGB").save(bio, "JPEG")
        bio.seek(0)

        await update.message.reply_photo(photo=bio)

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("⚠️ Oops! Something went wrong. Try another image.")

# Start Telegram bot
def run_bot():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN not set in environment variables")
    telegram_app = Application.builder().token(TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    telegram_app.run_polling()

if __name__ == "__main__":
    # Run Flask server in background (for Render)
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))
    )
    flask_thread.daemon = True
    flask_thread.start()

    # Run Telegram bot
    run_bot()
