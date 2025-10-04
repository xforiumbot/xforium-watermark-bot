Perfect — that means our code is finally **working**, now we just need to **tune the style** 🎯

Here’s what I’ll do based on what you said:

* 📏 **Make watermark ~10× bigger** — font size ~ **0.6 × image width** (very large).
* 📍 **Move it slightly to the right** — about **+20% horizontal offset**.
* 🌀 Keep the **15° tilt** and ~40% opacity.
* 🪄 Keep the faint shadow for visibility.

---

### 💥 Final Tuned Version — Replace `xforwatermark-bot.py` with this:

```python
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

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me an image and I'll watermark it with @xforium!")

# Watermark handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download image
        telegram_file = await update.message.photo[-1].get_file()
        photo_bytes = await telegram_file.download_as_bytearray()

        img = Image.open(BytesIO(photo_bytes)).convert("RGBA")
        width, height = img.size
        watermark_text = "@xforium"

        # MUCH larger font size (~60% of width)
        font_size = int(width * 0.6)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Transparent layer for watermark
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        # Text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Centered but shifted slightly right (~20% of width)
        x = (width - text_w) // 2 + int(width * 0.2)
        y = (height - text_h) // 2

        # Shadow (black) + main watermark (white, 40% opacity)
        draw.text((x + 5, y + 5), watermark_text, font=font, fill=(0, 0, 0, 120))
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 100))

        # Rotate ~15°
        rotated_layer = watermark_layer.rotate(-15, expand=True)

        # Center rotated watermark
        final_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        offset_x = (img.width - rotated_layer.width) // 2
        offset_y = (img.height - rotated_layer.height) // 2
        final_layer.paste(rotated_layer, (offset_x, offset_y), rotated_layer)

        # Merge
        watermarked_img = Image.alpha_composite(img, final_layer)

        # Save result
        output = BytesIO()
        output.name = "watermarked.jpg"
        watermarked_img.convert("RGB").save(output, "JPEG", quality=95)
        output.seek(0)

        await update.message.reply_photo(photo=output)
        logger.info("✅ Watermarked image sent successfully.")

    except Exception as e:
        logger.error(f"❌ Error watermarking image: {e}")
        await update.message.reply_text("⚠️ Failed to watermark image. Try again!")

# Run bot
def run_bot():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN is not set!")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling()

# Run Flask and bot
if __name__ == "__main__":
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
    ).start()
    run_bot()
```

---

### 📌 Notes:

* Font size is now **60% of image width** → very bold.
* Watermark is **centered** but nudged **20% to the right**.
* Visibility is much better thanks to shadow + opacity 100 (~40%).

---

🔥 **Try redeploying this now** and send a large image. You should see a *big, tilted, centered-right watermark* now.

Would you like me to make it **diagonally across the entire image** (like a security watermark)? That looks super professional for brands.
