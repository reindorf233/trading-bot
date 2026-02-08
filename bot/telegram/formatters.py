from datetime import datetime
from typing import Optional

from ..analysis.smc_engine_v4 import SMCAnalysisV4

class MessageFormatter:
    """Format analysis results for Telegram messages."""
    
    @staticmethod
    def format_signal_message(analysis: SMCAnalysisV4) -> str:
        """Format SMC analysis result into Telegram message."""
        
        # Helper function to escape special characters for Telegram
        def escape_markdown(text):
            return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
        
        # Signal emoji
        signal_emoji = "🟢" if analysis.signal in ["BUY", "SELL"] else "🔴"
        
        # Build message
        message = (
            f"{signal_emoji} **{escape_markdown(analysis.symbol)} Analysis**\n"
            f"🕐 {analysis.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📊 Timeframes: 4H | 30M | 5M\n\n"
            
            f"🎯 **SIGNAL: {escape_markdown(analysis.signal)}** (Confidence: {analysis.confidence}%)\n\n"
            
            f"📈 **MARKET BIAS:**\n"
            f"Direction: {escape_markdown(analysis.direction)}\n"
            f"4H Trend: {escape_markdown(analysis.trend_4h)}\n"
            f"4H Event: {escape_markdown(analysis.event_4h)}\n\n"
            
            f"🎯 **POINT OF INTEREST:**\n"
            f"Type: {escape_markdown(analysis.poi_type)}\n"
            f"Zone: {escape_markdown(analysis.poi_zone)}\n\n"
            
            f"💧 **LIQUIDITY:**\n"
            f"Sweep: {escape_markdown(analysis.liquidity_sweep)}\n"
            f"{escape_markdown(analysis.sweep_details)}\n\n"
            
            f"⚡ **CONFIRMATION:**\n"
            f"Pattern: {escape_markdown(analysis.confirmation_pattern)}\n\n"
            
            f"🤖 **AI ANALYSIS:**\n"
            f"Strategy: {escape_markdown(analysis.ai_reasons)}\n"
            f"Risk: {escape_markdown(analysis.risk_notes)}\n\n"
            
            f"⚠️ **DISCLAIMER:**\n"
            "Educational purposes only.\n"
            "Not financial advice. Trade at your own risk."
        )
        
        return message
    
    @staticmethod
    async def format_status_message(last_result: Optional[SMCAnalysisV4]) -> str:
        """Format status message with last analysis."""
        if not last_result:
            return "� No analysis performed yet. Use /analyze to start."
        
        # Escape special characters
        def escape_markdown(text):
            return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
        
        lines = [
            "📊 BOT STATUS",
            f"Last Analysis: {escape_markdown(last_result.symbol)}",
            f"Time: {last_result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Signal: {escape_markdown(last_result.signal)}",
            f"Confidence: {last_result.confidence}%",
            f"Bias: {escape_markdown(last_result.direction)}",
            ""
        ]
        
        if last_result.signal in ["BUY", "SELL"]:
            lines.extend([
                "Last Trade Plan:",
                f"Entry: {escape_markdown(last_result.entry_zone) or 'N/A'}",
                f"Invalidation: {escape_markdown(last_result.invalidation_level) or 'N/A'}",
                f"Target 1: {escape_markdown(last_result.target1) or 'N/A'}",
                f"Target 2: {escape_markdown(last_result.target2) or 'N/A'}",
            ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_help_message() -> str:
        """Format help message with bot commands."""
        return (
            "🤖 **CurrencyBot v2 - SMC Analysis**\n\n"
            "**Commands:**\n"
            "/start - Show main menu\n"
            "/analyze [SYMBOL] - Analyze a symbol (default: EURUSD)\n"
            "/set SYMBOL - Set default symbol\n"
            "/status - Show last analysis status\n"
            "/watch SYMBOL minutes - Schedule analysis\n"
            "/stopwatch - Stop scheduled analysis\n"
            "/help - Show this help message\n\n"
            "**Supported symbols:**\n"
            "• Forex: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD, EURGBP, EURJPY, GBPJPY, EURCHF, USDCAD\n"
            "• Crypto: BTCUSD, ETHUSD, LTCUSD, BCHUSD\n"
            "• Metals: XAUUSD, XAGUSD\n\n"
            "**Analysis Strategy:**\n"
            "1. Direction (4H bias) - BOS/MSS\n"
            "2. POI (30M) - OB/FVG/RB\n"
            "3. Liquidity Sweep - Into POI\n"
            "4. Confirmation (5M) - Entry patterns\n\n"
            "**JSON Output:**\n"
            "Add 'JSON signal' to any request for structured output\n\n"
            "⚠️ **Educational purposes only. Not financial advice.**"
        )
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """Format error message."""
        # Escape special characters in error message
        def escape_markdown(text):
            if not text:
                return text
            return str(text).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
        
        return f"❌ Error: {escape_markdown(error)}"
