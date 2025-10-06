import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def add_watermark(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("RGBA")
    watermark_text = "@xAutomation"

    # Create transparent layer for watermark
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Font size relative to image width
    font_size = int(image.width / 12)
    font = ImageFont.truetype("arial.ttf", font_size)

    # Get text size
    text_width, text_height = draw.textsize(watermark_text, font=font)

    # --- POSITION: bottom part of iPhone screen ---
    # Move watermark about 380-420px lower
    x = (image.width - text_width) / 2 - 30  # a little left
    y = image.height - text_height - 380     # significantly lower

    # --- STYLE: very low opacity and smaller angle ---
    angle = 80  # reduced angle
    watermark = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))
    draw_text = ImageDraw.Draw(watermark)
    draw_text.text((0, 0), watermark_text, fill=(255, 255, 255, 40), font=font)  # opacity ~15%

    # Rotate text
    watermark = watermark.rotate(angle, expand=1)
    txt_layer.paste(watermark, (int(x), int(y)), watermark)

    # Merge
    watermarked = Image.alpha_composite(image, txt_layer)

    # Convert back to bytes
    output = BytesIO()
    watermarked.convert("RGB").save(output, format="JPEG")
    output.seek(0)
    return output

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    image_bytes = await photo.download_as_bytearray()

    watermarked_image = await add_watermark(image_bytes)
    await update.message.reply_photo(photo=watermarked_image, caption="✅ Watermark added!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.run_polling()

if __name__ == "__main__":
    main()
