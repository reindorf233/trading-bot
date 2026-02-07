from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class Candle(BaseModel):
    """Candle data model."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

class MarketDataProvider(ABC):
    """Base class for market data providers."""
    
    @abstractmethod
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> List[Candle]:
        """Get candle data for a symbol and timeframe."""
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """Get available trading symbols."""
        pass
    
    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for provider."""
        pass

class DataProviderError(Exception):
    """Custom exception for data provider errors."""
    pass
