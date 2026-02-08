import logging
import asyncio
import signal
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import Config
from .providers import DerivProvider
from .analysis import SMCEngineV3
from .telegram.auth import AuthManager
from .telegram.formatters import MessageFormatter
from .storage import BotStorage
from .telegram.handlers import BotHandlers

logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot application."""
    
    def __init__(self):
        self.config = Config()
        self.application = None
        self.handlers = None
        
        # Initialize data provider - using Deriv
        self.provider = DerivProvider()
        
        self.smc_engine = SMCEngineV3(self.provider, self.config)
        self.storage = BotStorage()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        
        # Track scheduled jobs
        self.scheduled_jobs = {}  # user_id -> job_id
        
        # Setup handlers
        self.handlers = BotHandlers(self.config)
    
    async def start(self):
        """Start the bot."""
        try:
            # Validate configuration
            self.config.validate()
            logger.info("Configuration validated successfully")
            
            # Create Telegram application
            self.application = Application.builder().token(
                self.config.TELEGRAM_BOT_TOKEN
            ).build()
            
            # Setup handlers
            self.handlers.setup_handlers(self.application)
            
            # Start bot
            logger.info("Starting trading bot...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep the bot running
            try:
                # Run indefinitely
                while True:
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                logger.info("Stopping bot...")
                await self.stop()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot stopped")
    
    def run(self):
        """Run the bot with blocking call."""
        try:
            self.config.validate()
            logger.info("Starting trading bot...")
            
            # Create and setup application
            self.application = Application.builder().token(
                self.config.TELEGRAM_BOT_TOKEN
            ).build()
            
            # Setup handlers
            self.handlers.setup_handlers(self.application)
            
            # Start bot with blocking call
            logger.info("Starting trading bot...")
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Failed to run bot: {e}")
            raise

async def main():
    """Main entry point."""
    bot = TradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
