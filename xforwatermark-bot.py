# xforwatermark-bot.py

import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image  # Keep if your watermark logic uses Pillow
import io

# -----------------------------
# Flask app for Render health check
# -----------------------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is live!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# -----------------------------
# Telegram Bot setup
# -----------------------------
# Your bot token is already set in this variable
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

app = ApplicationBuilder().token(BOT_TOKEN).build()

# -----------------------------
# Command Handlers
# -----------------------------
async def start(update, context):
    await update.message.reply_text("Hello! Bot is live and responding!")

app.add_handler(CommandHandler("start", start))

# -----------------------------
# Message Handlers
# Replace this echo handler with your watermark logic
# -----------------------------
async def echo(update, context):
    # Example: replies with the same text
    await update.message.reply_text(update.message.text)

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Run Flask in a separate thread for Render health checks
    threading.Thread(target=run_flask).start()

    # Run Telegram bot in main thread
    print("🚀 Telegram bot is starting...")
    app.run_polling()  # Must run in main thread for PTB v21.4
