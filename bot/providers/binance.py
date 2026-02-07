"""
Binance data provider stub.
Placeholder for future crypto implementation.
"""
from typing import List
from .base import MarketDataProvider, Candle, DataProviderError

class BinanceProvider(MarketDataProvider):
    """Binance data provider for crypto (stub implementation)."""
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Binance."""
        # Convert to Binance format (e.g., EURUSD -> EURUSDT)
        normalized = symbol.replace("_", "")
        if not normalized.endswith("T"):
            normalized += "T"
        return normalized
    
    async def get_candles(self, symbol: str, timeframe: str, count: int = 500) -> List[Candle]:
        """Get candle data from Binance."""
        raise DataProviderError("Binance provider not implemented yet")
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols from Binance."""
        raise DataProviderError("Binance provider not implemented yet")
