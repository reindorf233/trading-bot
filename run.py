#!/usr/bin/env python3
"""
Convenient script to run the trading bot.
"""

import sys
import os
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))

if __name__ == "__main__":
    from bot.main import main
    main()
