# xforwatermark-bot.py

import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# -----------------------------
# Flask app for Render health check
# -----------------------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is live!"

def run_flask():
    # Run Flask on Render port
    flask_app.run(host="0.0.0.0", port=8080)

# -----------------------------
# Telegram Bot setup (your existing logic)
# -----------------------------
BOT_TOKEN = "8259315231:AAG_CJPN5XCYbstbA1j-JXw_QQJqTGR_rxs"  # <-- Replace with your BotFather token

app = ApplicationBuilder().token(BOT_TOKEN).build()

# -----------------------------
# Your existing handlers go here
# Example: start command
# -----------------------------
async def start(update, context):
    await update.message.reply_text("Hello! Bot is live and responding!")

app.add_handler(CommandHandler("start", start))

# Example echo handler (optional, keep your existing handlers)
async def echo(update, context):
    await update.message.reply_text(update.message.text)

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# -----------------------------
# Fix threading/asyncio issue
# -----------------------------
def run_bot():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start the bot using start_polling (async version)
    loop.run_until_complete(app.start_polling())
    loop.run_forever()

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Start Flask in a separate thread for Render health checks
    threading.Thread(target=run_flask).start()

    # Start Telegram bot in another thread with proper asyncio loop
    threading.Thread(target=run_bot, name="run_bot").start()
    
    print("🚀 Bot is running!")
