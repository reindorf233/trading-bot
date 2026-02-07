import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Data Provider Configuration
    DATA_PROVIDER: str = os.getenv("DATA_PROVIDER", "deriv")  # Deriv API
    
    # Deriv Configuration (Free API - no API key required)
    DERIV_API_KEY: str = os.getenv("DERIV_API_KEY", "")
    DERIV_APP_ID: str = os.getenv("DERIV_APP_ID", "1089")  # Demo app ID
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALLOWED_USER_ID: int = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))
    
    # Trading Configuration
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "EUR/USD")
    DEFAULT_RISK_R: float = float(os.getenv("DEFAULT_RISK_R", "2.0"))
    
    # AI Configuration (Optional)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Analysis Configuration
    SWING_LOOKBACK: int = 3
    FVG_TOLERANCE: float = 0.0001  # For FX pairs
    LIQUIDITY_TOLERANCE: float = 0.0005
    POI_PROXIMITY_CANDLES: int = 10  # 30M timeframe
    CONFIRMATION_PROXIMITY_CANDLES: int = 20  # 5M timeframe
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        required = [
            "TELEGRAM_BOT_TOKEN", 
            "TELEGRAM_ALLOWED_USER_ID"
        ]
        
        for key in required:
            if not getattr(cls, key):
                raise ValueError(f"Missing required environment variable: {key}")
        
        if cls.TELEGRAM_ALLOWED_USER_ID == 0:
            raise ValueError("TELEGRAM_ALLOWED_USER_ID must be set")
        
        # Validate data provider configuration
        # FMP provider works with demo key, no validation needed
        return True
