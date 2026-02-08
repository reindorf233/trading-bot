"""
Deriv API Provider
Free real-time trading data for forex, crypto, and synthetic indices
"""

import httpx
import asyncio
import json
import websockets
from typing import List, Optional
from datetime import datetime, timedelta

from .base import MarketDataProvider, Candle, DataProviderError
from ..config import Config


class DerivProvider(MarketDataProvider):
    """Deriv API provider for real-time trading data."""
    
    def __init__(self):
        self.config = Config()
        self.api_key = getattr(self.config, 'DERIV_API_KEY', '')
        self.app_id = getattr(self.config, 'DERIV_APP_ID', '125581')
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
        self.base_url = "https://api.deriv.com"
        
        # WebSocket connection state
        self.ws = None
        self.authorized = False
        
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
    
    async def _connect_websocket(self):
        """Connect to Deriv WebSocket API with symbol validation."""
        try:
            self.ws = await websockets.connect(self.ws_url)
            
            # Authorize if API key provided
            if self.use_api_key:
                auth_msg = {"authorize": self.api_key}
                await self.ws.send(json.dumps(auth_msg))
                
                # Wait for authorization response
                response = await self.ws.recv()
                auth_data = json.loads(response)
                
                if auth_data.get("error"):
                    raise DataProviderError(f"Deriv auth error: {auth_data['error']['message']}")
                
                self.authorized = True
                
                # Get active symbols to validate available pairs
                symbols_msg = {"active_symbols": "full"}
                await self.ws.send(json.dumps(symbols_msg))
                
                # Wait for symbols response
                symbols_response = await self.ws.recv()
                symbols_data = json.loads(symbols_response)
                
                if symbols_data.get("error"):
                    raise DataProviderError(f"Deriv symbols error: {symbols_data['error']['message']}")
                
                # Store available symbols for validation
                self.available_symbols = {}
                if "active_symbols" in symbols_data:
                    for symbol_data in symbols_data["active_symbols"]:
                        if isinstance(symbol_data, dict) and "symbol" in symbol_data:
                            symbol_name = symbol_data["symbol"]
                            display_name = symbol_data.get("display_name", symbol_name)
                            self.available_symbols[symbol_name] = display_name
                
                logger.info(f"Connected to Deriv WebSocket. Available symbols: {list(self.available_symbols.keys())[:10]}")
            
            return True
        except Exception as e:
            raise DataProviderError(f"Deriv WebSocket connection failed: {str(e)}")
    
    async def _get_candles_websocket(self, symbol: str, timeframe: str, count: int = 500) -> List[Candle]:
        """Get candle data using WebSocket API with symbol validation."""
        try:
            # Connect WebSocket
            await self._connect_websocket()
            
            # Normalize and validate symbol
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Validate symbol against available symbols
            deriv_symbol = self._validate_and_map_symbol(normalized_symbol)
            
            if not deriv_symbol:
                raise DataProviderError(f"Symbol {symbol} not available on Deriv. Available: {list(self.available_symbols.keys())[:10]}")
            
            # Map timeframe to Deriv granularity (in seconds)
            timeframe_map = {
                "1M": 60,
                "5M": 300, 
                "15M": 900,
                "30M": 1800,
                "1H": 3600,
                "4H": 14400,
                "1D": 86400
            }
            
            deriv_timeframe = timeframe_map.get(timeframe, 300)
            
            # Request candle data
            request_msg = {
                "ticks_history": deriv_symbol,
                "end": "latest",
                "count": count,
                "granularity": deriv_timeframe,
                "style": "candles"
            }
            
            await self.ws.send(json.dumps(request_msg))
            
            # Wait for response
            response = await self.ws.recv()
            data = json.loads(response)
            
            if data.get("error"):
                error_msg = data['error'].get('message', 'Unknown WebSocket error')
                raise DataProviderError(f"Deriv WebSocket error: {error_msg}")
            
            # Parse candles from response
            candles = []
            history_data = data.get("history", {}).get("prices", [])
            
            if not history_data:
                raise DataProviderError(f"No valid candle data found for {symbol} (WebSocket)")
            
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
            
            # Close WebSocket
            await self.ws.close()
            
            if not candles:
                raise DataProviderError(f"No valid candle data found for {symbol}")
            
            # Sort by timestamp (newest first)
            candles.sort(key=lambda x: x.timestamp, reverse=True)
            
            return candles[:count]
            
        except Exception as e:
            raise DataProviderError(f"Deriv WebSocket error: {str(e)}")
    
    def _validate_and_map_symbol(self, normalized_symbol: str) -> Optional[str]:
        """Validate symbol against available Deriv symbols and return mapped symbol."""
        # Direct symbol mapping for common pairs
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
            "EURCHF": "frxEURCHF",
            "BTCUSD": "CRYBTCUSD",
            "ETHUSD": "CRYETHUSD",
            "LTCUSD": "CRYLTCUSD",
            "BCHUSD": "CRYBCHUSD",
            "XAUUSD": "frxXAUUSD",
            "XAGUSD": "frxXAGUSD"
        }
        
        # Check direct mapping first
        if normalized_symbol in symbol_map:
            return symbol_map[normalized_symbol]
        
        # Check available symbols for crypto pairs
        if hasattr(self, 'available_symbols') and self.available_symbols:
            # Look for symbol in available symbols
            for available_symbol, display_name in self.available_symbols.items():
                if normalized_symbol == available_symbol or normalized_symbol == display_name:
                    # Try to find the correct mapped symbol
                    for mapped_symbol, mapped_name in symbol_map.items():
                        if available_symbol == mapped_name or display_name == mapped_name:
                            return mapped_symbol
            
            # Special handling for crypto symbols
            if normalized_symbol.startswith("BTC") and "BTC" in self.available_symbols:
                return "CRYBTCUSD"
            elif normalized_symbol.startswith("ETH") and "ETH" in self.available_symbols:
                return "CRYETHUSD"
            elif normalized_symbol.startswith("LTC") and "LTC" in self.available_symbols:
                return "CRYLTCUSD"
            elif normalized_symbol.startswith("BCH") and "BCH" in self.available_symbols:
                return "CRYBCHUSD"
        
        # Default mapping for forex pairs
        return f"frx{normalized_symbol}"
    
    async def _get_candles_fallback(self, symbol: str, timeframe: str, count: int = 500) -> List[Candle]:
        """Fallback method using free data sources."""
        try:
            # Try yfinance as fallback (free, no API key needed)
            import yfinance as yf
            
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Map to yfinance format
            yf_symbol = f"{normalized_symbol}=X"
            
            # Download data
            ticker = yf.Ticker(yf_symbol)
            
            # Determine period based on timeframe
            if timeframe in ["1M", "5M", "15M", "30M"]:
                period = "5d"
                interval = timeframe.replace("M", "m")
            elif timeframe in ["1H", "4H"]:
                period = "30d" 
                interval = timeframe.replace("H", "h")
            else:  # 1D
                period = "1y"
                interval = "1d"
            
            data = ticker.history(period=period, interval=interval)
            
            candles = []
            for index, row in data.iterrows():
                candle = Candle(
                    timestamp=index.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                candles.append(candle)
            
            if not candles:
                raise DataProviderError(f"No fallback data found for {symbol}")
            
            # Sort by timestamp (newest first)
            candles.sort(key=lambda x: x.timestamp, reverse=True)
            
            return candles[:count]
            
        except ImportError:
            raise DataProviderError("Fallback requires yfinance library: pip install yfinance")
        except Exception as e:
            raise DataProviderError(f"Fallback data error: {str(e)}")
    
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> List[Candle]:
        """Get candle data from Deriv with fallback."""
        try:
            # Try WebSocket first (primary method)
            return await self._get_candles_websocket(symbol, timeframe, count)
        except Exception as ws_error:
            # Fallback to HTTP method
            try:
                # Get symbol mapping for HTTP fallback
                normalized_symbol = self.normalize_symbol(symbol)
                
                # Map timeframe to Deriv granularity (in seconds)
                timeframe_map = {
                    "1M": 60,
                    "5M": 300, 
                    "15M": 900,
                    "30M": 1800,
                    "1H": 3600,
                    "4H": 14400,
                    "1D": 86400
                }
                
                deriv_timeframe = timeframe_map.get(timeframe, 300)
                
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
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v2/ticks_history",
                        params={
                            "ticks_history": deriv_symbol,
                            "adjust_start_time": 1,
                            "count": count,
                            "end": "latest",
                            "start": int((datetime.now() - timedelta(days=30)).timestamp()),
                            "style": "candles",
                            "granularity": deriv_timeframe
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("error"):
                            raise DataProviderError(f"Deriv HTTP error: {data['error']['message']}")
                        
                        # Parse response
                        candles = []
                        history_data = data.get("history", {}).get("prices", [])
                        
                        if not history_data:
                            raise DataProviderError(f"No valid candle data found for {symbol} (HTTP)")
                        
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
                                
                            except (ValueError, KeyError):
                                continue
                        
                        if candles:
                            candles.sort(key=lambda x: x.timestamp, reverse=True)
                            return candles[:count]
                    
            except Exception as http_error:
                # Final fallback to free data
                return await self._get_candles_fallback(symbol, timeframe, count)
            
            # If all methods fail, raise the original WebSocket error
            raise DataProviderError(f"Deriv API connection issue (likely method/URL mismatch) – falling back to alternative analysis: {str(ws_error)}")
    
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
            # Try WebSocket connection first
            await self._connect_websocket()
            if self.ws:
                await self.ws.close()
            return True
        except:
            # Fallback to HTTP test
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v2/ticks_history",
                        params={
                            "ticks_history": "frxEURUSD",
                            "count": 1,
                            "style": "candles",
                            "granularity": 60
                        },
                        timeout=10.0
                    )
                    return response.status_code == 200
            except:
                return False
