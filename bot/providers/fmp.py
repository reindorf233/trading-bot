"""
Financial Modeling Prep (FMP) Provider
Free stock market API with FX, crypto, and commodities data
"""

import httpx
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta

from .base import MarketDataProvider, Candle, DataProviderError
from ..config import Config


class FMPProvider(MarketDataProvider):
    """Financial Modeling Prep API provider."""
    
    def __init__(self):
        self.config = Config()
        self.api_key = getattr(self.config, 'FMP_API_KEY', '')
        self.base_url = "https://financialmodelingprep.com/stable"
        
        # FMP doesn't require API key for basic endpoints
        # But we'll support it if provided
        if not self.api_key:
            self.api_key = "demo"  # Use demo key
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to FMP format."""
        # Remove slashes, dashes, convert to uppercase
        normalized = symbol.replace("/", "").replace("-", "").upper()
        
        # Handle different asset types
        if len(normalized) == 6:  # FX pairs like EURUSD
            return normalized
        elif len(normalized) >= 7:  # Crypto pairs like BTCUSD
            return normalized
        elif normalized in ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"]:  # Metals
            return normalized
        else:
            # Default format
            if "/" not in normalized and len(normalized) >= 6:
                return normalized
            return normalized
    
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> List[Candle]:
        """Get candle data from FMP."""
        try:
            # Map timeframe to FMP parameters
            timeframe_map = {
                "5M": "1min",
                "30M": "5min", 
                "4H": "1hour",
                "1D": "historical-price-eod/full",
                "1W": "historical-price-eod/full"
            }
            
            fmp_timeframe = timeframe_map.get(timeframe, "1hour")
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Determine if crypto or forex
            is_crypto = any(crypto in normalized_symbol for crypto in ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOGE"])
            is_metal = any(metal in normalized_symbol for metal in ["XAU", "XAG", "XPT", "XPD"])
            
            # Build URL
            if is_crypto:
                # Crypto endpoint
                url = f"{self.base_url}/historical-chart/{fmp_timeframe}"
                params = {
                    "symbol": normalized_symbol,
                    "apikey": self.api_key
                }
            elif is_metal:
                # Metals use forex endpoints (commodities)
                url = f"{self.base_url}/historical-chart/{fmp_timeframe}"
                params = {
                    "symbol": normalized_symbol,
                    "apikey": self.api_key
                }
            else:
                # Forex endpoint
                if fmp_timeframe == "historical-price-eod/full":
                    url = f"{self.base_url}/historical-price-eod/full"
                else:
                    url = f"{self.base_url}/historical-chart/{fmp_timeframe}"
                
                params = {
                    "symbol": normalized_symbol,
                    "apikey": self.api_key
                }
            
            # Fetch data
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            
            # Parse response
            candles = []
            
            if isinstance(data, list) and data:
                for item in data[:count]:
                    try:
                        # Handle different response formats
                        if "date" in item:
                            timestamp_str = item["date"]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
                        elif "datetime" in item:
                            timestamp_str = item["datetime"]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            continue
                        
                        candle = Candle(
                            timestamp=timestamp,
                            open=float(item.get("open", 0)),
                            high=float(item.get("high", 0)),
                            low=float(item.get("low", 0)),
                            close=float(item.get("close", 0)),
                            volume=float(item.get("volume", 0))
                        )
                        candles.append(candle)
                        
                    except (ValueError, KeyError) as e:
                        continue
            
            # Sort by timestamp (newest first)
            candles.sort(key=lambda x: x.timestamp, reverse=True)
            
            return candles[:count]
            
        except httpx.HTTPStatusError as e:
            error_msg = f"FMP API error: {e.response.status_code}"
            raise DataProviderError(error_msg)
        except Exception as e:
            raise DataProviderError(f"Failed to fetch candles: {e}")
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols from FMP."""
        # FMP supports most major symbols
        return [
            # FX Pairs
            "EURUSD", "GBPUSD", "AUDUSD", "USDJPY", 
            "USDCAD", "NZDUSD", "EURGBP", "EURJPY",
            "GBPJPY", "AUDJPY", "EURCHF", "USDCHF",
            # Crypto Pairs (against USD)
            "BTCUSD", "ETHUSD", "BNBUSD", "ADAUSD",
            "SOLUSD", "XRPUSD", "DOGEUSD",
            # Metals (against USD)
            "XAUUSD",  # Gold
            "XAGUSD",  # Silver
            "XPTUSD",  # Platinum
            "XPDUSD"   # Palladium
        ]
