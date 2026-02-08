import logging
from typing import Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import Config
from ..providers import DerivProvider
from ..analysis import SMCEngine
from .auth import AuthManager
from .formatters import MessageFormatter
from ..storage import BotStorage

logger = logging.getLogger(__name__)

class BotHandlers:
    """Telegram bot command handlers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.auth = AuthManager(config)
        
        # Asset categories and pairs
        self.asset_categories = {
            "forex": {
                "name": "📈 Forex Pairs",
                "pairs": [
                    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
                    "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "USDCAD", "EURAUD"
                ]
            },
            "crypto": {
                "name": "🪙 Cryptocurrencies",
                "pairs": [
                    "BTCUSD", "ETHUSD", "BNBUSD", "ADAUSD", "SOLUSD", "XRPUSD",
                    "DOGEUSD", "MATICUSD", "DOTUSD", "AVAXUSD", "LINKUSD", "UNIUSD"
                ]
            },
            "metals": {
                "name": "🥇 Metals",
                "pairs": ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"]
            }
        }
        
        # Initialize data provider - using Deriv
        self.provider = DerivProvider()
            
        self.smc_engine = SMCEngine(self.provider, config)
        self.storage = BotStorage()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        
        # Track scheduled jobs
        self.scheduled_jobs = {}  # user_id -> job_id
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with modern menu."""
        if not await self.auth.check_access(update, context):
            return
        
        # Create main menu keyboard
        keyboard = [
            [
                InlineKeyboardButton("📈 Forex Pairs", callback_data="menu_forex"),
                InlineKeyboardButton("🪙 Crypto", callback_data="menu_crypto")
            ],
            [
                InlineKeyboardButton("🥇 Metals", callback_data="menu_metals"),
                InlineKeyboardButton("⚡ Quick Analysis", callback_data="quick_analyze")
            ],
            [
                InlineKeyboardButton("📊 My Status", callback_data="status"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🔗 Share Bot", callback_data="share_bot"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_msg = (
            "🤖 **Welcome to Trading Analysis Bot!**\n\n"
            "🌍 *Public Trading Analysis for Everyone*\n"
            "• 3-timeframe technical analysis\n"
            "• AI-powered strategy confirmation\n"
            "• Real-time market data\n"
            "• Forex, Crypto & Metals\n\n"
            "👇 *Choose an option below to get started:*\n\n"
            "🔗 **Share this bot with friends!**\n"
            "They can analyze any trading pair for free!"
        )
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
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
        
        await self.analyze_symbol(update, context, symbol)
    
    async def analyze_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Analyze a specific symbol using SMC strategy."""
        try:
            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            # Perform SMC analysis
            result = await self.smc_engine.analyze_symbol(symbol)
            
            # Format and send result
            message = MessageFormatter.format_signal_message(result)
            await update.message.reply_text(message, parse_mode="Markdown")
            
            # Store last result
            await self.storage.set_last_analysis(update.effective_user.id, result)
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            error_msg = MessageFormatter.format_error_message(f"Analysis failed: {str(e)}")
            await update.message.reply_text(error_msg, parse_mode="Markdown")
    
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
                result = await self.smc_engine.analyze_symbol(symbol)
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
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "menu_forex":
            await self.show_forex_menu(query)
        elif data == "menu_crypto":
            await self.show_crypto_menu(query)
        elif data == "menu_metals":
            await self.show_metals_menu(query)
        elif data == "quick_analyze":
            await self.quick_analyze(query)
        elif data == "status":
            await self.show_status(query)
        elif data == "settings":
            await self.show_settings(query)
        elif data == "share_bot":
            await self.share_bot(query)
        elif data == "help":
            await self.show_help(query)
        elif data.startswith("analyze_"):
            symbol = data.replace("analyze_", "")
            await self.analyze_symbol(query, symbol)
        elif data == "back_to_main":
            await self.show_main_menu(query)
    
    async def show_main_menu(self, query):
        """Show main menu."""
        keyboard = [
            [
                InlineKeyboardButton("📈 Forex Pairs", callback_data="menu_forex"),
                InlineKeyboardButton("🪙 Crypto", callback_data="menu_crypto")
            ],
            [
                InlineKeyboardButton("🥇 Metals", callback_data="menu_metals"),
                InlineKeyboardButton("⚡ Quick Analysis", callback_data="quick_analyze")
            ],
            [
                InlineKeyboardButton("📊 My Status", callback_data="status"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🔗 Share Bot", callback_data="share_bot"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_msg = (
            "🤖 **Trading Analysis Bot**\n\n"
            "👇 *Choose an option:*"
        )
        
        await query.edit_message_text(
            welcome_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def show_forex_menu(self, query):
        """Show forex pairs menu."""
        pairs = self.asset_categories["forex"]["pairs"]
        
        # Create keyboard with pairs in rows of 2
        keyboard = []
        for i in range(0, len(pairs), 2):
            row = []
            if i < len(pairs):
                row.append(InlineKeyboardButton(pairs[i], callback_data=f"analyze_{pairs[i]}"))
            if i + 1 < len(pairs):
                row.append(InlineKeyboardButton(pairs[i+1], callback_data=f"analyze_{pairs[i+1]}"))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📈 **Select Forex Pair:**\n\n*Choose a pair to analyze:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def show_crypto_menu(self, query):
        """Show crypto menu."""
        pairs = self.asset_categories["crypto"]["pairs"]
        
        keyboard = []
        for i in range(0, len(pairs), 2):
            row = []
            if i < len(pairs):
                row.append(InlineKeyboardButton(pairs[i], callback_data=f"analyze_{pairs[i]}"))
            if i + 1 < len(pairs):
                row.append(InlineKeyboardButton(pairs[i+1], callback_data=f"analyze_{pairs[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🪙 **Select Cryptocurrency:**\n\n*Choose a crypto to analyze:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def show_metals_menu(self, query):
        """Show metals menu."""
        pairs = self.asset_categories["metals"]["pairs"]
        
        keyboard = []
        for i in range(0, len(pairs), 2):
            row = []
            if i < len(pairs):
                row.append(InlineKeyboardButton(pairs[i], callback_data=f"analyze_{pairs[i]}"))
            if i + 1 < len(pairs):
                row.append(InlineKeyboardButton(pairs[i+1], callback_data=f"analyze_{pairs[i+1]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🥇 **Select Metal:**\n\n*Choose a metal to analyze:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def quick_analyze(self, query):
        """Quick analysis of default symbol."""
        symbol = self.config.DEFAULT_SYMBOL
        await self.analyze_symbol(query, symbol)
    
    async def analyze_symbol(self, query, symbol):
        """Analyze a specific symbol."""
        # Show loading message
        await query.edit_message_text(
            f"🔄 **Analyzing {symbol}...**\n\n*Please wait, this may take a few seconds.*",
            parse_mode="Markdown"
        )
        
        try:
            # Perform analysis
            result = await self.smc_engine.analyze_symbol(symbol)
            
            # Store result
            user_id = query.from_user.id
            await self.storage.save_analysis(result)
            
            # Format and send result
            message = MessageFormatter.format_signal_message(result)
            
            # Add back button to result
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            error_msg = MessageFormatter.format_error_message(str(e))
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                error_msg,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    async def show_status(self, query):
        """Show user status."""
        user_id = query.from_user.id
        
        # Get last analysis
        last_analysis = await self.storage.get_last_analysis(user_id)
        
        # Get scheduled jobs info
        job_info = ""
        if user_id in self.scheduled_jobs:
            job_id = self.scheduled_jobs[user_id]
            job = self.scheduler.get_job(job_id)
            if job:
                job_info = f"\n⏰ **Scheduled Analysis:** Every {job.trigger.interval} minutes"
        
        # Format status message
        status_msg = MessageFormatter.format_status_message(last_analysis)
        status_msg += job_info
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📊 **Your Status**\n\n{status_msg}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def show_settings(self, query):
        """Show settings menu."""
        keyboard = [
            [
                InlineKeyboardButton("📈 Set Default Symbol", callback_data="set_symbol"),
                InlineKeyboardButton("⏰ Set Watch List", callback_data="set_watch")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_msg = (
            "⚙️ **Settings**\n\n"
            "• Set default trading symbol\n"
            "• Configure watch lists\n"
            "• Analysis preferences\n\n"
            "*Choose an option below:*"
        )
        
        await query.edit_message_text(
            settings_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def show_help(self, query):
        """Show help information."""
        help_msg = MessageFormatter.format_help_message()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❓ **Help**\n\n{help_msg}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def share_bot(self, query):
        """Show bot sharing information."""
        bot_username = query.message.bot.username
        
        share_msg = (
            "🔗 **Share This Trading Bot!**\n\n"
            "🌍 *Free Trading Analysis for Everyone*\n\n"
            f"**Bot Username:** @{bot_username}\n\n"
            "📱 **How to share:**\n"
            "1. Click the button below\n"
            "2. Choose a friend or group\n"
            "3. Send the bot link\n\n"
            "✨ **Features your friends get:**\n"
            "• 📈 Forex, Crypto & Metals analysis\n"
            "• 🤖 AI-powered strategy confirmation\n"
            "• ⚡ Real-time market data\n"
            "• 🎯 Professional trading signals\n"
            "• 🆓 Completely FREE!\n\n"
            "🚀 *Start sharing professional trading analysis today!*"
        )
        
        # Create share button (this will open Telegram's share interface)
        keyboard = [
            [
                InlineKeyboardButton("🔗 Share Bot", url=f"https://t.me/{bot_username}")
            ],
            [
                InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            share_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
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
        
        # Add callback query handler for inline keyboards
        app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Handle unknown commands
        app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
