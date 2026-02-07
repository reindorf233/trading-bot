#!/usr/bin/env python3
"""
Simple script to start the trading bot
"""

import sys
import os
sys.path.append('bot')

def main():
    try:
        print("🚀 Starting Trading Bot...")
        print("📊 Bot Features:")
        print("  ✅ Alpha Vantage API integration")
        print("  ✅ FX, Crypto, and Metals support")
        print("  ✅ 3-timeframe analysis (4H, 30M, 5M)")
        print("  ✅ Private Telegram interface")
        print("")
        print("🔧 Configuration Status:")
        
        # Check configuration
        from bot.config import Config
        
        try:
            config = Config()
            
            # Check API keys
            if config.ALPHA_VANTAGE_API_KEY:
                print("  ✅ Alpha Vantage API: Configured")
            else:
                print("  ❌ Alpha Vantage API: Missing")
            
            if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_BOT_TOKEN != "your_telegram_bot_token_here":
                print("  ✅ Telegram Bot: Configured")
            else:
                print("  ❌ Telegram Bot: Missing")
            
            if config.TELEGRAM_ALLOWED_USER_ID and config.TELEGRAM_ALLOWED_USER_ID != 0:
                print(f"  ✅ User ID: {config.TELEGRAM_ALLOWED_USER_ID}")
            else:
                print("  ❌ User ID: Missing")
            
            print("")
            print("🎯 Starting bot now...")
            print("📱 Send commands to your bot on Telegram:")
            print("  /start - Initialize bot")
            print("  /analyze EURUSD - Analyze EUR/USD")
            print("  /analyze BTCUSD - Analyze Bitcoin")
            print("  /analyze XAUUSD - Analyze Gold")
            print("  /help - Show all commands")
            print("")
            print("🤖 Bot is running... Press Ctrl+C to stop")
            
            # Import and start bot
            from bot.main import main as bot_main
            bot_main()
            
        except Exception as e:
            print(f"\n❌ Configuration error: {e}")
            return

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        return

if __name__ == "__main__":
    main()
