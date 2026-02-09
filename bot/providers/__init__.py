"""
Data providers package
"""

from .base import MarketDataProvider, Candle, DataProviderError
from .deriv import DerivProvider

# Try to import market data provider, make it optional
try:
    from .market_data import MarketDataOnlineProvider
    MARKET_DATA_AVAILABLE = True
except ImportError:
    MarketDataOnlineProvider = None
    MARKET_DATA_AVAILABLE = False

__all__ = [
    'MarketDataProvider',
    'Candle', 
    'DataProviderError',
    'DerivProvider',
]

# Only include market data provider if available
if MARKET_DATA_AVAILABLE:
    __all__.append('MarketDataOnlineProvider')
