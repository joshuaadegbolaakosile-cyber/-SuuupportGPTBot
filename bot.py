import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

BOT_NAME = os.environ.get("BOT_NAME", "SuuupportGPTBot")

# Keyboard for main menu
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

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome_text = f"""
👋 **Hello {user.first_name}!**

Welcome to **{BOT_NAME}** - Your AI-Powered Support Assistant!

🚀 **Getting Started:**
• Send any message to start chatting
• Use the buttons below for quick actions
• Type /help to see all commands

What can I help you with today?
    """
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
📚 **Available Commands:**

• /start - Welcome message
• /help - Show this help
• /about - About this bot
• /reset - Clear conversation
• /feedback - Send feedback

💡 **Tips:**
• Just type any message to chat
• Use inline buttons for navigation
• Your feedback helps improve the bot!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = f"""
ℹ️ **About {BOT_NAME}**

**Version:** 2.0.0
**Status:** 🟢 Online

Built with Python + python-telegram-bot
Hosted on Railway
Open source on GitHub

🔗 https://github.com/yourusername/telegram-bot
    """
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command."""
    user_id = update.effective_user.id
    if user_id in context.user_data:
        context.user_data[user_id] = {}
    await update.message.reply_text(
        "🔄 **Conversation Reset!**\n\nYour chat history has been cleared.",
        parse_mode='Markdown'
    )

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /feedback command."""
    await update.message.reply_text(
        "💬 **Send Feedback**\n\n"
        "Please type your feedback message below.\n"
        "To cancel, type /cancel",
        parse_mode='Markdown'
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    await update.message.reply_text(
        "❌ **Cancelled!**\n\nUse /help to see available commands.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages."""
    user = update.effective_user
    message_text = update.message.text
    
    # Store user data
    user_id = user.id
    if user_id not in context.user_data:
        context.user_data[user_id] = {'count': 0}
    context.user_data[user_id]['count'] += 1
    
    # Send typing indicator
    await update.message.chat.send_action(action="typing")
    
    # Simple response
    response = f"""
📨 **You said:**
{message_text}

💡 **Tip:**
You've sent {context.user_data[user_id]['count']} messages!
Use /help to see all commands.
    """
    
    await update.message.reply_text(
        response,
        parse_mode='Markdown',
        reply_markup=get_keyboard()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "about":
        await about_command(update, context)
    elif query.data == "reset":
        user_id = query.from_user.id
        if user_id in context.user_data:
            context.user_data[user_id] = {}
        await query.message.reply_text("🔄 Reset complete!")
    elif query.data == "feedback":
        await query.message.reply_text(
            "💬 Please type your feedback message below.",
            parse_mode='Markdown'
        )
    
    await query.message.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ **Something went wrong!**\n\nPlease try again later.",
            parse_mode='Markdown'
        )

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("feedback", feedback_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add message handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start polling
    logger.info(f"{BOT_NAME} started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
