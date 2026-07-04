import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration from environment variables."""
    
    # Telegram Bot Token (required)
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required!")
    
    # Optional: OpenAI API Key for AI features
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Optional: Webhook URL for Railway
    WEBHOOK_URL = os.environ.get("RAILWAY_STATIC_URL", "")
    if not WEBHOOK_URL:
        # Fallback for local development
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://your-app.railway.app")
    
    # Bot settings
    BOT_NAME = os.environ.get("BOT_NAME", "SuuupportGPTBot")
    BOT_DESCRIPTION = os.environ.get("BOT_DESCRIPTION", "Your AI-Powered Support Assistant")
    
    # API settings
    API_TIMEOUT = int(os.environ.get("API_TIMEOUT", 30))
    MAX_MESSAGE_LENGTH = int(os.environ.get("MAX_MESSAGE_LENGTH", 4096))
    
    # Database (optional, for persistent storage)
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    
    # Redis (optional, for caching)
    REDIS_URL = os.environ.get("REDIS_URL", "")

config = Config()
