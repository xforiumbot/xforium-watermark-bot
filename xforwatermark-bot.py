import logging
import os
import threading
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageEnhance
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration via environment (easy to tweak in Render)
WATERMARK_FILE = os.getenv("WATERMARK_FILE", "watermark.png")    # file in repo root
WATERMARK_SCALE = float(os.getenv("WATERMARK_SCALE", "0.5"))     # fraction of image width (0.5 = 50%)
WATERMARK_OPACITY = float(os.getenv("WATERMARK_OPACITY", "0.9")) # 0.0..1.0

TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

@app.route("/")
def home():
    return "xForium watermark bot is running", 200

# Load watermark once at startup (so errors show in logs immediately)
BASE_DIR = Path(__file__).resolve().parent
watermark_path = BASE_DIR / WATERMARK_FILE
_loaded_wm = None

try:
    if not watermark_path.exists():
        raise FileNotFoundError(f"{watermark_path} not found")
    _loaded_wm = Image.open(watermark_path).convert("RGBA")
    logger.info(f"Loaded watermark image '{watermark_path.name}' size={_loaded_wm.size}")
except Exception as ex:
    logger.error(f"Could not load watermark image '{watermark_path}': {ex}")
    _loaded_wm = None

def prepare_watermark_for_image(base_img: Image.Image) -> Image.Image:
    """
    Resize, adjust opacity and rotate the watermark for the given base image.
    Returns a watermark Image in RGBA mode.
    """
    if _loaded_wm is None:
        raise RuntimeError("Watermark image not loaded on server")

    ow, oh = base_img.size
    # target width relative to base image
    target_w = max(1, int(ow * WATERMARK_SCALE))
    aspect = _loaded_wm.height / _loaded_wm.width
    target_h = max(1, int(target_w * aspect))

    wm = _loaded_wm.copy().resize((target_w, target_h), Image.LANCZOS)

    # apply opacity: change alpha channel brightness
    alpha = wm.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(WATERMARK_OPACITY)
    wm.putalpha(alpha)

    # rotate watermark (tilt)
    rotated = wm.rotate(-15, expand=True)
    return rotated

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a photo and I'll add your xForium watermark.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _loaded_wm is None:
        await update.message.reply_text("⚠️ Watermark image not found on server. Make sure 'watermark.png' is in the project root and redeploy.")
        return

    try:
        file = await update.message.photo[-1].get_file()
        data = await file.download_as_bytearray()
        base = Image.open(BytesIO(data)).convert("RGBA")
        bw, bh = base.size

        # Prepare watermark sized for this base image
        wm = prepare_watermark_for_image(base)
        wmw, wmh = wm.size

        # Position: centered vertically, slightly to the right horizontally
        # pos_x places watermark center around 60% width (tweak if needed)
        center_x = int(bw * 0.60)
        pos_x = center_x - wmw // 2
        pos_y = (bh - wmh) // 2

        # Ensure positions stay in bounds
        pos_x = max(-wmw, min(bw, pos_x))
        pos_y = max(-wmh, min(bh, pos_y))

        # Composite: create an empty layer and paste watermark with its alpha as mask
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(wm, (pos_x, pos_y), wm)

        combined = Image.alpha_composite(base, layer).convert("RGB")

        out = BytesIO()
        out.name = "watermarked.jpg"
        combined.save(out, format="JPEG", quality=95)
        out.seek(0)

        await update.message.reply_photo(photo=out, caption="✅ Watermarked by @xForium")
        logger.info("Sent watermarked image")
    except Exception as e:
        logger.exception("Failed to watermark image")
        await update.message.reply_text("⚠️ Failed to watermark image. Check server logs.")

def run_bot():
    if not TOKEN:
        logger.error("BOT_TOKEN not set in environment")
        return
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("Starting Telegram polling...")
    app_bot.run_polling()

if __name__ == "__main__":
    # start Flask in background (Render keep-alive)
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080))), daemon=True).start()
    run_bot()
