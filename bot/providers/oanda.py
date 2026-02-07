import httpx
from typing import List, Dict, Any
from datetime import datetime
import logging

from .base import MarketDataProvider, Candle, DataProviderError
from ..config import Config

logger = logging.getLogger(__name__)

class OandaProvider(MarketDataProvider):
    """OANDA REST API data provider."""
    
    def __init__(self):
        self.config = Config()
        self.headers = {
            "Authorization": f"Bearer {self.config.OANDA_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to OANDA format."""
        # Remove slashes, convert to uppercase, replace with underscore
        normalized = symbol.replace("/", "").replace("-", "").upper()
        
        # Insert underscore if not present and it's a standard FX pair
        if "_" not in normalized and len(normalized) == 6:
            normalized = normalized[:3] + "_" + normalized[3:]
        
        return normalized
    
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> List[Candle]:
        """Get candle data from OANDA."""
        try:
            # Map timeframe to OANDA granularity
            granularity_map = {
                "5M": "M5",
                "30M": "M30", 
                "4H": "H4",
                "1D": "D",
                "1W": "W"
            }
            
            if timeframe not in granularity_map:
                raise DataProviderError(f"Unsupported timeframe: {timeframe}")
            
            normalized_symbol = self.normalize_symbol(symbol)
            granularity = granularity_map[timeframe]
            
            url = f"{self.config.OANDA_BASE_URL}/instruments/{normalized_symbol}/candles"
            params = {
                "price": "M",  # Midpoint candles
                "granularity": granularity,
                "count": count
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if "candles" not in data or not data["candles"]:
                    raise DataProviderError(f"No candle data for {symbol}")
                
                candles = []
                for candle_data in data["candles"]:
                    if candle_data.get("complete", False):
                        candle = Candle(
                            timestamp=datetime.fromisoformat(candle_data["time"].replace("Z", "+00:00")),
                            open=float(candle_data["mid"]["o"]),
                            high=float(candle_data["mid"]["h"]),
                            low=float(candle_data["mid"]["l"]),
                            close=float(candle_data["mid"]["c"]),
                            volume=int(candle_data.get("volume", 0))
                        )
                        candles.append(candle)
                
                # Return newest candles first (reverse if needed)
                candles.sort(key=lambda x: x.timestamp, reverse=True)
                return candles
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OANDA API error: {e.response.status_code} - {e.response.text}")
            raise DataProviderError(f"OANDA API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            raise DataProviderError(f"Failed to fetch candles: {str(e)}")
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols from OANDA."""
        try:
            url = f"{self.config.OANDA_BASE_URL}/accounts/{self.config.OANDA_ACCOUNT_ID}/instruments"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                instruments = data.get("instruments", [])
                
                # Filter for FX pairs and major instruments
                fx_symbols = []
                for instrument in instruments:
                    name = instrument.get("name", "")
                    if "_" in name and len(name) == 7:  # Standard FX format like EUR_USD
                        fx_symbols.append(name)
                
                return sorted(fx_symbols)
                
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            # Return default major pairs if API fails
            return [
                "EUR_USD", "GBP_USD", "AUD_USD", "USD_JPY", 
                "USD_CAD", "NZD_USD", "EUR_GBP", "EUR_JPY"
            ]
