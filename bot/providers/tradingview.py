"""
TradingView data provider stub.
Placeholder for future implementation using tvDatafeed.
"""
from typing import List
from .base import MarketDataProvider, Candle, DataProviderError

class TradingViewProvider(MarketDataProvider):
    """TradingView data provider (stub implementation)."""
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for TradingView."""
        # TradingView uses various formats, implement as needed
        return symbol.replace("_", "")
    
    async def get_candles(self, symbol: str, timeframe: str, count: int = 500) -> List[Candle]:
        """Get candle data from TradingView."""
        raise DataProviderError("TradingView provider not implemented yet")
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols from TradingView."""
        raise DataProviderError("TradingView provider not implemented yet")
