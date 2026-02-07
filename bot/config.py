import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Data Provider Configuration
    DATA_PROVIDER: str = os.getenv("DATA_PROVIDER", "fmp")  # "oanda", "alphavantage", or "fmp"
    
    # OANDA Configuration
    OANDA_API_KEY: str = os.getenv("OANDA_API_KEY", "")
    OANDA_ACCOUNT_ID: str = os.getenv("OANDA_ACCOUNT_ID", "")
    OANDA_ENVIRONMENT: str = os.getenv("OANDA_ENVIRONMENT", "practice")
    OANDA_BASE_URL: str = "https://api-fxpractice.oanda.com/v3" if OANDA_ENVIRONMENT == "practice" else "https://api-fxtrade.oanda.com/v3"
    
    # Alpha Vantage Configuration
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    
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
        if cls.DATA_PROVIDER == "oanda" and not cls.OANDA_API_KEY:
            raise ValueError("OANDA_API_KEY required when using OANDA provider")
        
        if cls.DATA_PROVIDER == "alphavantage" and not cls.ALPHA_VANTAGE_API_KEY:
            raise ValueError("ALPHA_VANTAGE_API_KEY required when using Alpha Vantage provider")
        
        return True
