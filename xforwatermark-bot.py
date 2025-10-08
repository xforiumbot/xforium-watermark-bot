import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Your bot token
BOT_TOKEN = "8259315231:AAFGTbqrn8bz7goeVb0N5vJpo-ZA4RVBrbo"

# Path to your watermark image (ensure watermark.png is in the same folder as this file)
WATERMARK_PATH = "watermark.png"

async def add_watermark(input_image: BytesIO) -> BytesIO:
    original = Image.open(input_image).convert("RGBA")

    # Load watermark
    watermark = Image.open(WATERMARK_PATH).convert("RGBA")

    # ✅ Resize watermark to ~70% of original width (smaller & cleaner)
    new_width = int(original.width * 0.7)
    aspect_ratio = watermark.height / watermark.width
    new_height = int(new_width * aspect_ratio)
    watermark = watermark.resize((new_width, new_height), Image.LANCZOS)

    # ✅ Rotate watermark to ~80° (slightly tilted)
    watermark = watermark.rotate(80, expand=1)

    # ✅ Make watermark super light (opacity)
    alpha = watermark.split()[3]
    alpha = alpha.point(lambda p: p * 0.08)  # ~8% opacity
    watermark.putalpha(alpha)

    # ✅ Place watermark near the bottom (iPhone screenshots) but slightly lifted (~0.6 inch)
    margin_x = int(original.width * 0.05)  # ~5% from left
    margin_y = int(original.height * 0.17)  # ~17% from bottom (higher than before)

    position = (margin_x, original.height - watermark.height - margin_y)

    # Paste watermark
    watermarked = Image.new("RGBA", original.size)
    watermarked.paste(original, (0, 0))
    watermarked.paste(watermark, position, mask=watermark)

    output = BytesIO()
    watermarked.convert("RGB").save(output, format="JPEG", quality=95)
    output.seek(0)
    return output

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = BytesIO()
    await file.download_to_memory(out=image_bytes)
    image_bytes.seek(0)

    watermarked_image = await add_watermark(image_bytes)
    await update.message.reply_photo(photo=watermarked_image, caption="✅ Watermark added!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an image 📸 and I'll watermark it instantly!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.COMMAND, start))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
