from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from ..config import Config

class AuthManager:
    """Manage user authentication for the bot."""
    
    def __init__(self, config: Config):
        self.config = config
        self.allowed_user_id = config.TELEGRAM_ALLOWED_USER_ID
    
    async def is_authorized(self, update: Update) -> bool:
        """Check if user is authorized to use the bot."""
        if not update.effective_user:
            return False
        
        # Allow all users - public bot
        return True
    
    async def check_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check access and send unauthorized message if needed."""
        if not await self.is_authorized(update):
            await update.message.reply_text(
                "⚠️ Access denied. Please contact the bot administrator."
            )
            return False
        
        return True
