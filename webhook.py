import os
import logging
import json
from flask import Flask, request, jsonify
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize bot and dispatcher
bot = Bot(token=config.BOT_TOKEN)
dispatcher = Dispatcher(bot, update_queue=None, use_context=True)

# Global keyboard
def get_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📚 Help", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ],
        [
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
            InlineKeyboardButton("💬 Feedback", callback_data="feedback")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Handlers
async def start(update, context):
    user = update.effective_user
    welcome_text = f"""
👋 **Hello {user.first_name}!**

Welcome to **SuuupportGPTBot** - Your AI-Powered Support Assistant!

🚀 **Getting Started:**
• Send any message to start
• Use the menu below
• Type /help for commands
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_keyboard())

async def help_command(update, context):
    help_text = """
📚 **Commands:**
• /start - Welcome
• /help - This help
• /about - About bot
• /reset - Reset chat
• /feedback - Send feedback
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update, context):
    about_text = """
ℹ️ **SuuupportGPTBot v2.0**

Built with Python + python-telegram-bot
Hosted on Railway
Open source on GitHub
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def reset_command(update, context):
    await update.message.reply_text("🔄 Conversation reset!", parse_mode='Markdown')

async def handle_message(update, context):
    text = update.message.text
    response = f"📨 You said: {text}\n\n💡 Use /help for assistance!"
    await update.message.reply_text(response, reply_markup=get_keyboard())

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "about":
        await about_command(update, context)
    elif query.data == "reset":
        await query.message.reply_text("🔄 Reset complete!")
    
    await query.message.delete()

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("about", about_command))
dispatcher.add_handler(CommandHandler("reset", reset_command))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
dispatcher.add_handler(CallbackQueryHandler(button_callback))

@app.route(f"/webhook/{config.BOT_TOKEN}", methods=["POST"])
def webhook():
    """Handle incoming webhook updates."""
    try:
        update_data = request.get_json()
        update = Update.de_json(update_data, bot)
        dispatcher.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "bot": config.BOT_NAME,
        "version": "2.0.0"
    })

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """Set webhook URL."""
    webhook_url = f"{config.WEBHOOK_URL}/webhook/{config.BOT_TOKEN}"
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/setWebhook"
    
    try:
        import requests
        response = requests.post(url, json={"url": webhook_url})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
