import logging
import asyncio
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
import requests
import json

# Import configuration
from config import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_ACTION = 0
WAITING_FEEDBACK = 1

class SupportBot:
    """Main bot class with all handlers."""
    
    def __init__(self):
        self.application = None
        self.user_data: Dict[int, Dict] = {}
        
    def get_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📚 Help", callback_data="help"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ],
            [
                InlineKeyboardButton("🔄 Reset", callback_data="reset"),
                InlineKeyboardButton("💬 Feedback", callback_data="feedback")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("🌐 Website", url="https://github.com/yourusername/yourrepo")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        welcome_text = f"""
👋 **Hello {user.first_name}!**

Welcome to **SuuupportGPTBot** - Your AI-Powered Support Assistant!

✨ **Features:**
• 🧠 Intelligent support responses
• 📝 Quick commands and shortcuts
• 🔒 Secure and private conversations
• ⚡ 24/7 availability

🚀 **Getting Started:**
1. Send any message to start a conversation
2. Use the menu below for quick actions
3. Type /help to see all commands

What can I help you with today?
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=self.get_keyboard()
        )
        
        # Log user interaction
        logger.info(f"User {user.id} ({user.username}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📚 **Available Commands:**

**General:**
• /start - Start the bot and see welcome message
• /help - Show this help message
• /about - Learn about this bot
• /reset - Clear conversation history

**Support:**
• /feedback - Send feedback to developers
• /stats - View your usage statistics (coming soon)

**Tips:**
• Just type any message to chat with the bot
• Use inline buttons for quick navigation
• The bot remembers conversation context

🛠 **Need more help?**
Contact: @your_support_username
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command."""
        about_text = """
ℹ️ **About SuuupportGPTBot**

**Version:** 2.0.0
**Status:** 🟢 Online

**🤖 What is this bot?**
SuuupportGPTBot is an intelligent support assistant designed to help users with various queries and tasks.

**✨ Key Features:**
• AI-powered responses (when configured)
• User-friendly interface
• Quick and responsive
• Secure and private

**🛠 Technology Stack:**
• Python 3.11
• python-telegram-bot
• Railway (hosting)
• OpenAI API (optional)

**📝 Open Source:**
This bot is open-source! Check the code on GitHub:
🔗 [https://github.com/yourusername/telegram-support-bot](https://github.com/yourusername/telegram-support-bot)

**💡 Support:**
For issues or suggestions, open a GitHub issue or contact @your_support_username
        """
        await update.message.reply_text(about_text, parse_mode='Markdown')
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command."""
        user_id = update.effective_user.id
        if user_id in context.user_data:
            context.user_data[user_id] = {}
        await update.message.reply_text(
            "🔄 **Conversation Reset!**\n\nYour chat history has been cleared. Start fresh with /start",
            parse_mode='Markdown'
        )
    
    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feedback command."""
        await update.message.reply_text(
            "💬 **Share Your Feedback!**\n\n"
            "Please send your feedback, suggestions, or bug reports. "
            "I'll forward it to the developers.\n\n"
            "To cancel, type /cancel",
            parse_mode='Markdown'
        )
        return WAITING_FEEDBACK
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        # Initialize user data if not exists
        if user_id not in context.user_data:
            context.user_data[user_id] = {
                'history': [],
                'message_count': 0
            }
        
        # Update user data
        context.user_data[user_id]['message_count'] += 1
        context.user_data[user_id]['history'].append({
            'role': 'user',
            'content': message_text
        })
        
        # Keep only last 10 messages for context
        if len(context.user_data[user_id]['history']) > 10:
            context.user_data[user_id]['history'] = context.user_data[user_id]['history'][-10:]
        
        # Send typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Process message based on features
        response = await self.generate_response(
            message_text, 
            context.user_data[user_id]['history']
        )
        
        # Send response with keyboard
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=self.get_keyboard()
        )
        
        logger.info(f"User {user_id}: {message_text[:50]}...")
    
    async def generate_response(self, message: str, history: list) -> str:
        """Generate response with or without AI."""
        
        # If OpenAI API key is configured, use AI
        if config.OPENAI_API_KEY:
            try:
                import openai
                openai.api_key = config.OPENAI_API_KEY
                
                # Prepare messages for OpenAI
                messages = [
                    {"role": "system", "content": (
                        "You are SuuupportGPTBot, a friendly and helpful support assistant. "
                        "Provide clear, concise, and actionable responses. "
                        "Be professional but approachable. "
                        "If you don't know something, be honest about it."
                    )}
                ]
                
                # Add conversation history
                for msg in history[-5:]:  # Last 5 messages for context
                    messages.append(msg)
                
                # Add current message
                messages.append({"role": "user", "content": message})
                
                # Get AI response
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7,
                    timeout=config.API_TIMEOUT
                )
                
                ai_response = response.choices[0].message.content.strip()
                
                # Add AI response to history
                history.append({
                    'role': 'assistant',
                    'content': ai_response
                })
                
                return ai_response
                
            except Exception as e:
                logger.error(f"AI generation error: {e}")
                return (
                    "⚠️ I'm having trouble generating an AI response right now. "
                    "Here are some things I can help with:\n\n"
                    "• Use /help to see all commands\n"
                    "• Check the menu below for quick actions\n"
                    "• Try rephrasing your question\n\n"
                    "I'll be back to full capacity soon! 💪"
                )
        
        # Fallback: Simple echo bot with helpful tips
        tips = [
            "Did you know you can use /help to see all commands? 🤔",
            "Tip: Use the menu buttons for quick navigation! 🎯",
            "Want to reset the conversation? Just use /reset 🔄",
            "Your feedback helps me improve! Use /feedback to share 💬"
        ]
        import random
        tip = random.choice(tips)
        
        return (
            f"📨 **You said:**\n{message}\n\n"
            f"💡 **Tip:** {tip}\n\n"
            "Configure an AI API key to get smarter responses!\n"
            "Check the README on GitHub for setup instructions."
        )
    
    async def feedback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle feedback messages."""
        feedback = update.message.text
        
        # Here you can send feedback to a channel or store in database
        logger.info(f"Feedback received: {feedback}")
        
        # Acknowledge receipt
        await update.message.reply_text(
            "✅ **Thank you for your feedback!**\n\n"
            "Your input helps improve this bot. "
            "We'll review it as soon as possible.\n\n"
            "If you have more to share, just send another message!",
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def cancel_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command."""
        await update.message.reply_text(
            "❌ **Cancelled!**\n\nUse /help to see available commands.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button presses."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Handle different button actions
        if query.data == "help":
            await self.help_command(update, context)
            await query.message.delete()
            
        elif query.data == "about":
            await self.about_command(update, context)
            await query.message.delete()
            
        elif query.data == "reset":
            if user_id in context.user_data:
                context.user_data[user_id] = {}
            await query.message.reply_text(
                "🔄 **Reset Complete!**\n\nYour conversation has been cleared.",
                parse_mode='Markdown'
            )
            await query.message.delete()
            
        elif query.data == "feedback":
            await query.message.reply_text(
                "💬 Please type your feedback message below.\n\n"
                "To cancel, type /cancel",
                parse_mode='Markdown'
            )
            await query.message.delete()
            return WAITING_FEEDBACK
            
        elif query.data == "stats":
            await self.show_stats(query, context)
            await query.message.delete()
    
    async def show_stats(self, query, context):
        """Show user statistics."""
        user_id = query.from_user.id
        user_data = context.user_data.get(user_id, {})
        message_count = user_data.get('message_count', 0)
        
        stats_text = f"""
📊 **Your Statistics**

👤 User ID: `{user_id}`
💬 Messages sent: {message_count}
📅 First interaction: {user_data.get('first_seen', 'N/A')}
📌 Last activity: {user_data.get('last_seen', 'N/A')}

💡 Tip: Your conversation history helps me provide better responses!
        """
        await query.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Notify user about error
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ **Oops! Something went wrong.**\n\n"
                "I've logged this error and the developers will look into it. "
                "Please try again in a moment.\n\n"
                "If the problem persists, use /feedback to report it.",
                parse_mode='Markdown'
            )
    
    def setup_handlers(self):
        """Set up all handlers for the bot."""
        # Create application
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("about", self.about_command))
        self.application.add_handler(CommandHandler("reset", self.reset_command))
        self.application.add_handler(CommandHandler("feedback", self.feedback_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_handler))
        
        # Add conversation handler for feedback
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("feedback", self.feedback_command),
                CallbackQueryHandler(self.button_callback, pattern="feedback")
            ],
            states={
                WAITING_FEEDBACK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.feedback_handler)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_handler)]
        )
        self.application.add_handler(conv_handler)
        
        # Add message handler for text messages
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        # Add callback handler for inline buttons
        self.application.add_handler(
            CallbackQueryHandler(self.button_callback)
        )
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
    
    def run(self):
        """Run the bot."""
        self.setup_handlers()
        
        # Start the bot
        logger.info("Starting SuuupportGPTBot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main entry point."""
    bot = SupportBot()
    bot.run()

if __name__ == "__main__":
    main()
