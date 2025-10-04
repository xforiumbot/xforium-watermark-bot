import logging
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for Render health check
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is running!", 200

TOKEN = os.getenv("BOT_TOKEN")

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me an image and I'll watermark it with @xforium!")

# --- Handle Photo ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        telegram_file = await update.message.photo[-1].get_file()
        photo_bytes = await telegram_file.download_as_bytearray()

        img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
        width, height = img.size
        watermark_text = "@xforium"

        # Dynamic font size (20% of width)
        font_size = int(width * 0.2)

        # Try loading a TTF font, else fallback
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Create transparent layer for watermark
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        # Get text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = (height - text_h) // 2

        # Add shadow (black, slight offset)
        draw.text((x+3, y+3), watermark_text, font=font, fill=(0, 0, 0, 100))
        # Add watermark (white, ~40% opacity)
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 100))

        # Rotate watermark layer
        rotated_layer = watermark_layer.rotate(-15, expand=True)

        # Composite layers with proper centering
        final_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        offset_x = (img.width - rotated_layer.width) // 2
        offset_y = (img.height - rotated_layer.height) // 2
        final_layer.paste(rotated_layer, (offset_x, offset_y), rotated_layer)

        # Merge watermark with original
        watermarked_img = Image.alpha_composite(img, final_layer)

        # Save and send back
        output = BytesIO()
        output.name = "watermarked.jpg"
        watermarked_img.convert("RGB").save(output, "JPEG", quality=95)
        output.seek(0)

        await update.message.reply_photo(photo=output)
        logger.info("✅ Watermarked image sent successfully.")

    except Exception as e:
        logger.error(f"❌ Error watermarking image: {e}")
        await update.message.reply_text("⚠️ Failed to watermark image. Try again!")

# --- Run Bot ---
def run_bot():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN is not set!")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling()

# --- Start Flask & Bot ---
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))).start()
    run_bot()

