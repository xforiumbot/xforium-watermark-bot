import os
from flask import Flask, request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ✅ Your bot token (already inserted)
BOT_TOKEN = "8259315231:AAFGTbqrn8bz7goeVb0N5vJpo-ZA4RVBrbo"

# ✅ Your Render URL (already inserted, do NOT change)
WEBHOOK_URL = "https://xforium-watermark-bot.onrender.com"  

app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ✅ Watermark logic
def add_watermark(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("RGBA")
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    font_size = int(min(image.size) / 17)  # ✅ Slightly smaller watermark
    font = ImageFont.truetype("arial.ttf", font_size)

    text = "@xAutomation"
    text_width, text_height = draw.textsize(text, font=font)

    # ✅ Position: Bottom zone (iPhone ratio) + 0.6 inch higher from bottom
    y_offset = int(image.height * 0.06)  
    x = (image.width - text_width) / 2
    y = image.height - text_height - y_offset

    # ✅ Draw text (low opacity)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 30))

    # ✅ Rotate watermark
    rotated_txt = txt_layer.rotate(80, expand=1)
    watermarked = Image.alpha_composite(image, rotated_txt)

    # ✅ Enhance brightness
    enhancer = ImageEnhance.Brightness(watermarked)
    watermarked = enhancer.enhance(1)

    output = BytesIO()
    watermarked.convert("RGB").save(output, format="JPEG")
    output.seek(0)
    return output

# ✅ Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me a screenshot, and I’ll watermark it!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    watermarked_image = add_watermark(photo_bytes)
    await update.message.reply_photo(photo=watermarked_image)

# ✅ Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, handle_image))

# ✅ Webhook endpoints
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot is live and running!"

# ✅ Auto set webhook on startup
async def set_webhook():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
