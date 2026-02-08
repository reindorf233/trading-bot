from datetime import datetime
from typing import Optional

from ..analysis.smc_engine import SMCAnalysis

class MessageFormatter:
    """Format analysis results for Telegram messages."""
    
    @staticmethod
    def format_signal_message(result: SignalResult) -> str:
        """Format complete signal analysis result."""
        
        # Helper function to escape special characters for Telegram
        def escape_markdown(text):
            return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
        
        # Signal emoji
        signal_emoji = "🟢" if result.decision in ["BUY", "SELL"] else "🔴"
        
        # Build message
        message = (
            f"{signal_emoji} **{escape_markdown(result.symbol)} Analysis**\n"
            f"🕐 {result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📊 Timeframes: 4H | 30M | 5M\n\n"
            
            f"🎯 **SIGNAL: {escape_markdown(result.decision)}** (Confidence: {result.confidence}%)\n\n"
            
            f"📈 **MARKET BIAS:**\n"
            f"Direction: {escape_markdown(result.bias)}\n"
            f"4H Trend: {escape_markdown(result.trend_4h)}\n"
            f"4H Event: {escape_markdown(result.bos_mss_4h)}\n\n"
            
            f"🎯 **POINT OF INTEREST:**\n"
            f"Type: {escape_markdown(result.poi_type) or 'None'}\n"
            f"Zone: {escape_markdown(result.poi_zone) or 'N/A'}\n\n"
            
            f"💧 **LIQUIDITY:**\n"
            f"Sweep: {'Yes' if result.liquidity_sweep else 'No'}\n"
            f"{escape_markdown(result.sweep_details or '')}\n\n"
            
            f"⚡ **CONFIRMATION:**\n"
            f"Pattern: {escape_markdown(result.confirmation_pattern) or 'None'}\n\n"
            
            f"🤖 **AI ANALYSIS:**\n"
            f"Strategy: {escape_markdown(result.ai_reasons or '')}\n"
            f"Risk: {escape_markdown(result.risk_notes or '')}\n\n"
            
            f"⚠️ **DISCLAIMER:**\n"
            "Educational purposes only.\n"
            "Not financial advice. Trade at your own risk."
        )
        
        return message
    
    @staticmethod
    def format_status_message(last_result: Optional[SMCAnalysis]) -> str:
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
