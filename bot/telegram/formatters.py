from datetime import datetime
from typing import Optional

from ..analysis.signal_engine import SignalResult

class MessageFormatter:
    """Format analysis results for Telegram messages."""
    
    @staticmethod
    def format_signal_message(result: SignalResult) -> str:
        """Format complete signal analysis result."""
        
        # Determine emoji based on decision
        if result.decision == "BUY":
            emoji = "🟢"
            signal = "✅ BUY"
        elif result.decision == "SELL":
            emoji = "🔴"
            signal = "✅ SELL"
        else:
            emoji = "⚠️"
            signal = "⚠️ NO TRADE"
        
        # Build message sections
        lines = [
            f"{emoji} {result.symbol} Analysis",
            f"🕐 {result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
            f"📊 Timeframes: 4H | 30M | 5M",
            "",
            f"🎯 SIGNAL: {signal} (Confidence: {result.confidence}%)",
            ""
        ]
        
        # Bias section
        lines.extend([
            "📈 MARKET BIAS:",
            f"Direction: {result.bias}",
            f"4H Trend: {result.trend_4h}",
            f"4H Event: {result.bos_mss_4h}",
        ])
        
        if result.swing_high_4h:
            lines.append(f"Swing High: {result.swing_high_4h:.5f}")
        if result.swing_low_4h:
            lines.append(f"Swing Low: {result.swing_low_4h:.5f}")
        
        lines.append("")
        
        # POI section
        lines.extend([
            "🎯 POINT OF INTEREST:",
            f"Type: {result.poi_type or 'None'}",
            f"Zone: {result.poi_zone or 'N/A'}",
        ])
        
        if result.poi_strength:
            lines.append(f"Strength: {result.poi_strength:.2f}")
        
        lines.append("")
        
        # Liquidity section
        lines.extend([
            "💧 LIQUIDITY:",
            f"Sweep: {'Yes' if result.liquidity_sweep else 'No'}",
        ])
        
        if result.sweep_details:
            details = result.sweep_details
            lines.extend([
                f"Pool Type: {details.get('type', 'N/A')}",
                f"Sweep Price: {details.get('sweep_price', 'N/A')}",
            ])
        
        lines.append("")
        
        # Confirmation section
        lines.extend([
            "⚡ CONFIRMATION:",
            f"Pattern: {result.confirmation_pattern or 'None'}",
        ])
        
        if result.confirmation_confidence:
            lines.append(f"Confidence: {result.confirmation_confidence:.2f}")
        
        lines.append("")
        
        # Trade plan (only for trade signals)
        if result.decision in ["BUY", "SELL"] and result.entry_zone:
            lines.extend([
                "💼 TRADE PLAN:",
                f"Entry Zone: {result.entry_zone}",
                f"Invalidation: {result.invalidation_level or 'N/A'}",
                f"Target 1: {result.target1 or 'N/A'}",
                f"Target 2: {result.target2 or 'N/A'}",
                ""
            ])
        
        # AI Analysis section
        lines.extend([
            "🤖 AI ANALYSIS:",
        ])
        
        for aspect, reason in result.ai_reasons.items():
            lines.append(f"{aspect.title()}: {reason}")
        
        if result.missing_conditions:
            lines.append("Missing: " + ", ".join(result.missing_conditions))
        
        if result.risk_notes:
            lines.append(f"Risk: {result.risk_notes}")
        
        lines.append("")
        
        # Disclaimer
        lines.extend([
            "⚠️ DISCLAIMER:",
            "This analysis is for educational purposes only.",
            "Not financial advice. Trade at your own risk."
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_status_message(last_result: Optional[SignalResult]) -> str:
        """Format status message with last analysis."""
        if not last_result:
            return "📊 No analysis performed yet. Use /analyze to start."
        
        lines = [
            "📊 BOT STATUS",
            f"Last Analysis: {last_result.symbol}",
            f"Time: {last_result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Signal: {last_result.decision}",
            f"Confidence: {last_result.confidence}%",
            f"Bias: {last_result.bias}",
            ""
        ]
        
        if last_result.decision in ["BUY", "SELL"]:
            lines.extend([
                "Last Trade Plan:",
                f"Entry: {last_result.entry_zone or 'N/A'}",
                f"Invalidation: {last_result.invalidation_level or 'N/A'}",
                f"Target 1: {last_result.target1 or 'N/A'}",
                f"Target 2: {last_result.target2 or 'N/A'}",
            ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_help_message() -> str:
        """Format help message with bot commands."""
        return (
            "🤖 TRADING ASSISTANT BOT\n"
            "Commands:\n"
            "/start - Start using the bot\n"
            "/analyze [SYMBOL] - Analyze a symbol (default: EURUSD)\n"
            "/set SYMBOL - Set default symbol\n"
            "/status - Show last analysis status\n"
            "/watch SYMBOL minutes - Schedule analysis (e.g., /watch EURUSD 30)\n"
            "/stopwatch - Stop scheduled analysis\n"
            "/help - Show this help message\n"
            "\n"
            "Supported symbols: EURUSD, GBPUSD, AUDUSD, USDJPY, USDCAD, NZDUSD\n"
            "Format: EURUSD, EUR/USD, or EUR_USD all work\n"
            "\n"
            "⚠️ This bot provides analysis only, not financial advice."
        )
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """Format error message."""
        return f"❌ Error: {error}"
