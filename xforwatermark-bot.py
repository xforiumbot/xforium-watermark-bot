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

# Store watermark text per user (default: @xforium)
WATERMARKS = {}

# Flask app for Render port requirement
app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Bot is running!', 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send an image to watermark with @xforium! Use /settext to change the watermark.')

async def settext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text('Please provide text, e.g., /settext MyWatermark')
        return
    WATERMARKS[user_id] = ' '.join(context.args)
    await update.message.reply_text(f'Watermark set to: {WATERMARKS[user_id]}')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get photo
        photo = await update.message.photo[-1].get_file()
        photo_bytes = await photo.download_as_bytearray()

        # Open image
        img = Image.open(BytesIO(photo_bytes)).convert('RGBA')
        draw = ImageDraw.Draw(img)

        # Get user-specific watermark or default
        user_id = update.message.from_user.id
        watermark_text = WATERMARKS.get(user_id, '@xforium')

        # Watermark settings
        font_size = 36
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Position: center-right (vertically centered, 10px from right)
        width, height = img.size
        position = (width - text_width - 10, (height - text_height) // 2)

        # Draw semi-transparent white background
        bg_position = (position[0] - 5, position[1] - 5, width - 5, position[1] + text_height + 5)
        draw.rectangle(bg_position, fill=(255, 255, 255, 128))

        # Draw white text
        draw.text(position, watermark_text, fill=(255, 255, 255, 255), font=font)

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
    telegram_app.add_handler(CommandHandler("settext", settext))
    telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    telegram_app.run_polling()

if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080))))
    flask_thread.daemon = True
    flask_thread.start()
    # Run Telegram bot
    run_bot()
