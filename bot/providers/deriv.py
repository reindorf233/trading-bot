"""
Deriv API Provider
Free real-time trading data for forex, crypto, and synthetic indices
"""

import httpx
import asyncio
import json
from typing import List, Optional
from datetime import datetime, timedelta

from .base import MarketDataProvider, Candle, DataProviderError
from ..config import Config


class DerivProvider(MarketDataProvider):
    """Deriv API provider for real-time trading data."""
    
    def __init__(self):
        self.config = Config()
        self.api_key = getattr(self.config, 'DERIV_API_KEY', '')
        self.app_id = getattr(self.config, 'DERIV_APP_ID', '1089')  # Demo app ID
        self.base_url = "https://api.deriv.com"
        self.ws_url = "wss://ws.derivws.com/websockets/v3"
        
        # Deriv doesn't require API key for basic endpoints
        if not self.api_key:
            self.use_api_key = False
        else:
            self.use_api_key = True
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to Deriv format."""
        # Remove slashes, dashes, convert to uppercase
        normalized = symbol.replace("/", "").replace("-", "").upper()
        
        # Handle different asset types
        if len(normalized) == 6:  # FX pairs like EURUSD
            return normalized
        elif len(normalized) >= 7:  # Crypto pairs like BTCUSD
            return normalized
        elif normalized in ["XAUUSD", "XAGUSD"]:  # Metals
            return normalized
        else:
            return normalized
    
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> List[Candle]:
        """Get candle data from Deriv."""
        # Map timeframe to Deriv parameters
        timeframe_map = {
            "1M": "1",
            "5M": "5", 
            "15M": "15",
            "30M": "30",
            "1H": "60",
            "4H": "240",
            "1D": "D"
        }
        
        deriv_timeframe = timeframe_map.get(timeframe, "60")
        normalized_symbol = self.normalize_symbol(symbol)
        
        # Deriv symbol mapping
        symbol_map = {
            "EURUSD": "frxEURUSD",
            "GBPUSD": "frxGBPUSD", 
            "USDJPY": "frxUSDJPY",
            "USDCHF": "frxUSDCHF",
            "AUDUSD": "frxAUDUSD",
            "NZDUSD": "frxNZDUSD",
            "EURGBP": "frxEURGBP",
            "EURJPY": "frxEURJPY",
            "GBPJPY": "frxGBPJPY",
            "USDCAD": "frxUSDCAD",
            "EURAUD": "frxEURAUD",
            "BTCUSD": "CRYBTCUSD",
            "ETHUSD": "CRYETHUSD",
            "XAUUSD": "frxXAUUSD",
            "XAGUSD": "frxXAGUSD"
        }
        
        deriv_symbol = symbol_map.get(normalized_symbol, f"frx{normalized_symbol}")
        
        # Build request
        request_data = {
            "ticks_history": deriv_symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "start": (datetime.now() - timedelta(days=30)).timestamp(),
            "style": "candles",
            "granularity": int(deriv_timeframe)
        }
        
        # Fetch data
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v2/ticks",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("error"):
                        raise DataProviderError(f"Deriv API error: {data['error']['message']}")
                    
                    # Parse response
                    candles = []
                    history_data = data.get("history", {}).get("prices", [])
                    
                    for item in history_data:
                        try:
                            timestamp = datetime.fromtimestamp(item["epoch"])
                            
                            candle = Candle(
                                timestamp=timestamp,
                                open=float(item["open"]),
                                high=float(item["high"]),
                                low=float(item["low"]),
                                close=float(item["close"]),
                                volume=int(item.get("volume", 0))
                            )
                            candles.append(candle)
                            
                        except (ValueError, KeyError) as e:
                            continue
                    
                    if not candles:
                        raise DataProviderError(f"No valid candle data found for {symbol}")
                    
                    # Sort by timestamp (newest first)
                    candles.sort(key=lambda x: x.timestamp, reverse=True)
                    
                    return candles[:count]
                    
                else:
                    raise DataProviderError(f"Deriv API error: {response.status_code}")
                    
            except httpx.HTTPError as e:
                raise DataProviderError(f"HTTP error fetching data: {str(e)}")
            except Exception as e:
                raise DataProviderError(f"Error fetching data from Deriv: {str(e)}")
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols from Deriv."""
        # Deriv supports most major symbols
        return [
            # FX Pairs
            "EURUSD", "GBPUSD", "AUDUSD", "USDJPY", 
            "USDCAD", "NZDUSD", "EURGBP", "EURJPY",
            "GBPJPY", "AUDJPY", "EURCHF", "USDCHF",
            # Crypto Pairs (against USD)
            "BTCUSD", "ETHUSD", "LTCUSD", "BCHUSD",
            # Metals
            "XAUUSD", "XAGUSD"
        ]
    
    async def test_connection(self) -> bool:
        """Test connection to Deriv API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v2/active_symbols",
                    timeout=10.0
                )
                return response.status_code == 200
        except:
            return False
