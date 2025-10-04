import os
from io import BytesIO
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
WATERMARK_PATH = "Black_White_Simple_Quote_Instagram_Post-removebg-preview.png"  # PNG watermark file

# === /start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a photo and I’ll watermark it ✍️")

# === Function to add image watermark ===
def add_watermark(input_image_bytes):
    base_image = Image.open(BytesIO(input_image_bytes)).convert("RGBA")

    # Open watermark image
    watermark = Image.open(WATERMARK_PATH).convert("RGBA")

    # --- Resize watermark to ~35% of base image width ---
    target_width = int(base_image.width * 0.35)  # ✅ 3.5× bigger than before
    aspect_ratio = watermark.height / watermark.width
    new_height = int(target_width * aspect_ratio)
    watermark = watermark.resize((target_width, new_height), Image.LANCZOS)

    # --- Adjust watermark opacity ---
    alpha = watermark.split()[3]
    alpha = alpha.point(lambda p: p * 0.85)  # ✅ 85% opacity (more visible but still transparent)
    watermark.putalpha(alpha)

    # --- Position: centered and slightly to the right ---
    pos_x = int(base_image.width / 2 + base_image.width * 0.1 - watermark.width / 2)
    pos_y = int(base_image.height / 2 - watermark.height / 2)

    # --- Paste watermark ---
    watermarked = base_image.copy()
    watermarked.paste(watermark, (pos_x, pos_y), watermark)

    # Convert back to bytes
    output_bytes = BytesIO()
    watermarked.convert("RGB").save(output_bytes, format="JPEG")
    output_bytes.seek(0)
    return output_bytes

# === Handle images ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()

    watermarked_bytes = add_watermark(photo_bytes)

    await update.message.reply_photo(photo=watermarked_bytes, caption="✅ Watermark added!")

# === MAIN ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🚀 Bot is running...")
    app.run_polling()
