import logging
from typing import Optional
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import Config
from ..providers import FMPProvider
from ..analysis import SignalEngine
from .auth import AuthManager
from .formatters import MessageFormatter
from ..storage import BotStorage

logger = logging.getLogger(__name__)

class BotHandlers:
    """Telegram bot command handlers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.auth = AuthManager(config)
        
        # Initialize data provider based on configuration
        if config.DATA_PROVIDER == "alphavantage":
            self.provider = AlphaVantageProvider()
        elif config.DATA_PROVIDER == "fmp":
            self.provider = FMPProvider()
        else:
            self.provider = OandaProvider()
            
        self.signal_engine = SignalEngine(self.provider, config)
        self.storage = BotStorage()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        
        # Track scheduled jobs
        self.scheduled_jobs = {}  # user_id -> job_id
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not await self.auth.check_access(update, context):
            return
        
        welcome_msg = (
            "🤖 Welcome to your Private Trading Assistant!\n\n"
            "I analyze FX pairs using 3-timeframe framework:\n"
            "• 4H for market bias\n"
            "• 30M for POI detection\n"
            "• 5M for entry confirmation\n\n"
            f"Default symbol: {self.config.DEFAULT_SYMBOL}\n\n"
            "Use /analyze to get started or /help for commands."
        )
        
        await update.message.reply_text(welcome_msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not await self.auth.check_access(update, context):
            return
        
        help_msg = MessageFormatter.format_help_message()
        await update.message.reply_text(help_msg)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command."""
        if not await self.auth.check_access(update, context):
            return
        
        # Get symbol from command or use default
        if context.args:
            symbol = context.args[0]
        else:
            symbol = self.config.DEFAULT_SYMBOL
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🔄 Analyzing {symbol}...\nThis may take a few seconds."
        )
        
        try:
            # Perform analysis
            result = await self.signal_engine.analyze_symbol(symbol)
            
            # Store result
            await self.storage.save_analysis(result)
            
            # Format and send result
            message = MessageFormatter.format_signal_message(result)
            await processing_msg.edit_text(message)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            error_msg = MessageFormatter.format_error_message(str(e))
            await processing_msg.edit_text(error_msg)
    
    async def set_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /set command to set default symbol."""
        if not await self.auth.check_access(update, context):
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /set SYMBOL\nExample: /set EURUSD"
            )
            return
        
        symbol = context.args[0]
        
        try:
            # Validate symbol by trying to normalize it
            normalized = self.provider.normalize_symbol(symbol)
            
            # Save user preference
            user_id = update.effective_user.id
            await self.storage.set_user_symbol(user_id, symbol)
            
            await update.message.reply_text(
                f"✅ Default symbol set to: {symbol}\n"
                f"Normalized format: {normalized}"
            )
            
        except Exception as e:
            error_msg = MessageFormatter.format_error_message(f"Invalid symbol: {str(e)}")
            await update.message.reply_text(error_msg)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not await self.auth.check_access(update, context):
            return
        
        user_id = update.effective_user.id
        
        # Get last analysis
        last_analysis = await self.storage.get_last_analysis(user_id)
        
        # Get scheduled jobs info
        job_info = ""
        if user_id in self.scheduled_jobs:
            job_id = self.scheduled_jobs[user_id]
            job = self.scheduler.get_job(job_id)
            if job:
                job_info = f"\n⏰ Scheduled analysis: Every {job.trigger.interval} minutes"
        
        # Format status message
        status_msg = MessageFormatter.format_status_message(last_analysis)
        status_msg += job_info
        
        await update.message.reply_text(status_msg)
    
    async def watch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /watch command for scheduled analysis."""
        if not await self.auth.check_access(update, context):
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /watch SYMBOL MINUTES\n"
                "Example: /watch EURUSD 30"
            )
            return
        
        symbol = context.args[0]
        try:
            interval = int(context.args[1])
            if interval < 5 or interval > 1440:  # 5 min to 24 hours
                raise ValueError("Interval must be between 5 and 1440 minutes")
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid interval: {str(e)}")
            return
        
        user_id = update.effective_user.id
        
        # Remove existing job if any
        if user_id in self.scheduled_jobs:
            old_job_id = self.scheduled_jobs[user_id]
            self.scheduler.remove_job(old_job_id)
        
        # Add new scheduled job
        job_id = f"watch_{user_id}_{datetime.now().timestamp()}"
        
        async def scheduled_analysis():
            try:
                result = await self.signal_engine.analyze_symbol(symbol)
                await self.storage.save_analysis(result)
                
                # Send result to user
                message = MessageFormatter.format_signal_message(result)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message
                )
                
            except Exception as e:
                logger.error(f"Scheduled analysis failed: {e}")
                error_msg = MessageFormatter.format_error_message(str(e))
                await context.bot.send_message(
                    chat_id=user_id,
                    text=error_msg
                )
        
        # Schedule the job
        self.scheduler.add_job(
            scheduled_analysis,
            trigger=IntervalTrigger(minutes=interval),
            id=job_id,
            name=f"Analysis for {user_id}",
            replace_existing=True
        )
        
        # Track job
        self.scheduled_jobs[user_id] = job_id
        
        await update.message.reply_text(
            f"✅ Scheduled analysis set:\n"
            f"Symbol: {symbol}\n"
            f"Interval: Every {interval} minutes\n"
            f"Use /stopwatch to cancel."
        )
    
    async def stopwatch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stopwatch command to cancel scheduled analysis."""
        if not await self.auth.check_access(update, context):
            return
        
        user_id = update.effective_user.id
        
        if user_id not in self.scheduled_jobs:
            await update.message.reply_text("ℹ️ No scheduled analysis to stop.")
            return
        
        job_id = self.scheduled_jobs[user_id]
        
        try:
            self.scheduler.remove_job(job_id)
            del self.scheduled_jobs[user_id]
            await update.message.reply_text("✅ Scheduled analysis stopped.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error stopping schedule: {str(e)}")
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands."""
        if not await self.auth.check_access(update, context):
            return
        
        await update.message.reply_text(
            "❓ Unknown command. Use /help for available commands."
        )
    
    def setup_handlers(self, app: Application):
        """Setup all command handlers."""
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("analyze", self.analyze_command))
        app.add_handler(CommandHandler("set", self.set_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("watch", self.watch_command))
        app.add_handler(CommandHandler("stopwatch", self.stopwatch_command))
        
        # Handle unknown commands
        app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
