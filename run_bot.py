#!/usr/bin/env python3
"""
Trading Bot Entry Point
Runs the trading bot with proper module imports
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the bot
if __name__ == "__main__":
    from bot.main import main
    main()
