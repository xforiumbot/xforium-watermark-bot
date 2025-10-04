import logging
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask for Render health check
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is alive!", 200

# Telegram token
TOKEN = os.getenv("BOT_TOKEN")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me an image — I’ll watermark it with @xforium!")

# Watermark logic
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # 1️⃣ Get the photo
        file = await update.message.photo[-1].get_file()
        image_bytes = await file.download_as_bytearray()
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        width, height = img.size

        # 2️⃣ Watermark text
        watermark_text = "@xforium"
        font_size = int(min(width, height) * 0.15)  # about 15% of image size

        # 3️⃣ Load font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # 4️⃣ Create transparent layer
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # Text size and position (center)
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        x = (width - text_w) // 2
        y = (height - text_h) // 2

        # 5️⃣ Draw watermark text with ~30% opacity (77 out of 255)
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 90))

        # 6️⃣ Rotate watermark layer ~15°
        rotated_txt = txt_layer.rotate(-15, expand=1)

        # 7️⃣ Paste rotated watermark back centered
        new_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        offset_x = (img.width - rotated_txt.width) // 2
        offset_y = (img.height - rotated_txt.height) // 2
        new_layer.paste(rotated_txt, (offset_x, offset_y), rotated_txt)

        # 8️⃣ Combine layers
        final_img = Image.alpha_composite(img, new_layer)

        # 9️⃣ Send watermarked image
        output = BytesIO()
        output.name = "watermarked.jpg"
        final_img.convert("RGB").save(output, "JPEG", quality=95)
        output.seek(0)

        await update.message.reply_photo(photo=output)
        logger.info("✅ Watermarked image sent!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await update.message.reply_text("⚠️ Something went wrong watermarking your image.")

# Start Telegram bot
def run_bot():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN not set.")
    app_telegram = Application.builder().token(TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_telegram.run_polling()

# Run Flask and Bot
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))).start()
    run_bot()
